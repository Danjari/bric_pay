from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
import logging
from datetime import datetime
import threading

from src.models import User, Transaction, TransactionType
from src.schemas import DepositRequest, DepositResponse
from src.utils import TransactionManager, atomic_operation, with_connection_retry

logger = logging.getLogger(__name__)

class DepositService:
    """Service class for deposit-related operations with enhanced transaction management"""
    
    # Thread-local storage for tracking concurrent deposits
    _deposit_locks = threading.local()
    
    @staticmethod
    def _get_deposit_lock(account_number: str) -> threading.Lock:
        """Get or create a lock for an account number"""
        if not hasattr(DepositService._deposit_locks, 'locks'):
            DepositService._deposit_locks.locks = {}
        
        if account_number not in DepositService._deposit_locks.locks:
            DepositService._deposit_locks.locks[account_number] = threading.Lock()
        
        return DepositService._deposit_locks.locks[account_number]
    
    @staticmethod
    @with_connection_retry(max_retries=3)
    @atomic_operation("Fund deposit to account")
    def deposit_funds(db: Session, deposit_data: DepositRequest) -> DepositResponse:
        """
        Deposit funds to a user account with enhanced atomic operations and concurrent access handling
        
        Args:
            db (Session): Database session
            deposit_data (DepositRequest): Deposit data
            
        Returns:
            DepositResponse: Deposit result with updated balance
            
        Raises:
            ValueError: If account not found or invalid amount
        """
        # Acquire lock for the account to prevent concurrent modifications
        account_lock = DepositService._get_deposit_lock(deposit_data.account_number)
        
        try:
            # Acquire lock with timeout
            if not account_lock.acquire(timeout=10):
                raise ValueError(f"Timeout acquiring lock for account {deposit_data.account_number}")
            
            logger.info(f"Deposit: Lock acquired for account {deposit_data.account_number}")
            
            # Find the user account
            user = db.query(User).filter_by(account_number=deposit_data.account_number).first()
            
            if not user:
                raise ValueError(f"Account {deposit_data.account_number} not found")
            
            # Get initial balance for logging
            initial_balance = float(user.balance) if user.balance else 0.0
            
            # Verify account is still valid (double-check after lock acquisition)
            db.refresh(user)
            
            # Update account balance
            user.update_balance(deposit_data.amount)
            
            # Create transaction record
            transaction = Transaction(
                from_account=None,  # Deposits don't have a source account
                to_account=deposit_data.account_number,
                amount=deposit_data.amount,
                transaction_type=TransactionType.DEPOSIT,
                created_at=datetime.now()
            )
            
            # Save changes atomically (commit happens in atomic_operation decorator)
            db.add(transaction)
            
            # Get final balance for response
            final_balance = float(user.balance)
            
            logger.info(f"Deposit of ${deposit_data.amount:.2f} successful for account {deposit_data.account_number}")
            logger.info(f"Balance change: ${initial_balance:.2f} -> ${final_balance:.2f}")
            
            return DepositResponse(
                account_number=deposit_data.account_number,
                new_balance=final_balance,
                deposited_amount=deposit_data.amount,
                message=f"Successfully deposited ${deposit_data.amount:.2f}"
            )
            
        except ValueError as e:
            # Re-raise ValueError for business logic errors
            logger.warning(f"Deposit failed - business logic error: {e}")
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Deposit failed - unexpected error: {e}")
            raise ValueError(f"Failed to process deposit: {str(e)}")
        finally:
            # Always release lock
            try:
                account_lock.release()
                logger.debug(f"Deposit: Lock released for account {deposit_data.account_number}")
            except Exception as e:
                logger.error(f"Error releasing lock for deposit to account {deposit_data.account_number}: {e}")
    
    @staticmethod
    @with_connection_retry(max_retries=2)
    def get_account_balance(db: Session, account_number: str) -> float:
        """
        Get current balance for an account with connection retry
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            
        Returns:
            float: Current balance
            
        Raises:
            ValueError: If account not found
        """
        try:
            user = db.query(User).filter_by(account_number=account_number).first()
            
            if not user:
                raise ValueError(f"Account {account_number} not found")
            
            return float(user.balance) if user.balance else 0.0
        except Exception as e:
            logger.error(f"Error getting balance for account {account_number}: {e}")
            raise
    
    @staticmethod
    def get_concurrent_deposit_status(db: Session, account_number: str) -> dict:
        """
        Get information about concurrent deposits for an account
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            
        Returns:
            dict: Concurrent deposit information
        """
        try:
            # Check if there are any active deposit transactions for this account
            from datetime import timedelta
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            
            active_deposits = db.query(Transaction).filter(
                Transaction.to_account == account_number,
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.created_at >= one_minute_ago
            ).count()
            
            # Get lock status
            lock = DepositService._get_deposit_lock(account_number)
            lock_acquired = lock.locked()
            
            return {
                "account_number": account_number,
                "active_deposits_last_minute": active_deposits,
                "lock_acquired": lock_acquired,
                "lock_owner": threading.current_thread().name if lock_acquired else None
            }
        except Exception as e:
            logger.error(f"Error getting concurrent deposit status for account {account_number}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def validate_deposit_preconditions(db: Session, deposit_data: DepositRequest) -> dict:
        """
        Validate all preconditions for a deposit without executing it
        
        Args:
            db (Session): Database session
            deposit_data (DepositRequest): Deposit data
            
        Returns:
            dict: Validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "account_info": {}
        }
        
        try:
            # Check account exists
            user = db.query(User).filter_by(account_number=deposit_data.account_number).first()
            if not user:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Account {deposit_data.account_number} not found")
            else:
                current_balance = float(user.balance) if user.balance else 0.0
                new_balance = current_balance + deposit_data.amount
                
                validation_result["account_info"] = {
                    "exists": True,
                    "current_balance": current_balance,
                    "deposit_amount": deposit_data.amount,
                    "new_balance": new_balance
                }
            
            # Check for concurrent access
            account_lock = DepositService._get_deposit_lock(deposit_data.account_number)
            if account_lock.locked():
                validation_result["warnings"].append(f"Account {deposit_data.account_number} is currently being used in another operation")
            
            # Check database connection health
            if not TransactionManager.check_connection_health(db):
                validation_result["warnings"].append("Database connection health check failed")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result 