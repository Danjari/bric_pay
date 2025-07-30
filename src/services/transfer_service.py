from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import and_
import logging
from datetime import datetime
import uuid
import threading
from typing import Optional

from src.models import User, Transaction, TransactionType
from src.schemas import TransferRequest, TransferResponse
from src.utils import TransactionManager, atomic_operation, with_connection_retry

logger = logging.getLogger(__name__)

class TransferService:
    """Service class for transfer-related operations with enhanced transaction management"""
    
    # Thread-local storage for tracking concurrent transfers
    _transfer_locks = threading.local()
    
    @staticmethod
    def _get_transfer_lock(account_number: str) -> threading.Lock:
        """Get or create a lock for an account number"""
        if not hasattr(TransferService._transfer_locks, 'locks'):
            TransferService._transfer_locks.locks = {}
        
        if account_number not in TransferService._transfer_locks.locks:
            TransferService._transfer_locks.locks[account_number] = threading.Lock()
        
        return TransferService._transfer_locks.locks[account_number]
    
    @staticmethod
    @with_connection_retry(max_retries=3)
    @atomic_operation("Fund transfer between accounts")
    def transfer_funds(db: Session, transfer_data: TransferRequest) -> TransferResponse:
        """
        Transfer funds between accounts with enhanced atomic operations and concurrent access handling
        
        Args:
            db (Session): Database session
            transfer_data (TransferRequest): Transfer data
            
        Returns:
            TransferResponse: Transfer result with updated balances
            
        Raises:
            ValueError: If accounts not found, insufficient balance, or other validation errors
        """
        # Generate unique transfer ID
        transfer_id = str(uuid.uuid4())
        
        # Acquire locks for both accounts to prevent concurrent modifications
        from_lock = TransferService._get_transfer_lock(transfer_data.from_account)
        to_lock = TransferService._get_transfer_lock(transfer_data.to_account)
        
        # Acquire locks in consistent order to prevent deadlocks
        if transfer_data.from_account < transfer_data.to_account:
            first_lock, second_lock = from_lock, to_lock
            first_account, second_account = transfer_data.from_account, transfer_data.to_account
        else:
            first_lock, second_lock = to_lock, from_lock
            first_account, second_account = transfer_data.to_account, transfer_data.from_account
        
        try:
            # Acquire locks with timeout
            if not first_lock.acquire(timeout=10):
                raise ValueError(f"Timeout acquiring lock for account {first_account}")
            if not second_lock.acquire(timeout=10):
                first_lock.release()
                raise ValueError(f"Timeout acquiring lock for account {second_account}")
            
            logger.info(f"Transfer {transfer_id}: Locks acquired for accounts {transfer_data.from_account} and {transfer_data.to_account}")
            
            # Find both accounts with row-level locking simulation
            from_user = db.query(User).filter_by(account_number=transfer_data.from_account).first()
            to_user = db.query(User).filter_by(account_number=transfer_data.to_account).first()
            
            # Validate accounts exist
            if not from_user:
                raise ValueError(f"Source account {transfer_data.from_account} not found")
            if not to_user:
                raise ValueError(f"Destination account {transfer_data.to_account} not found")
            
            # Check sufficient balance with proper decimal handling
            from_balance = float(from_user.balance) if from_user.balance else 0.0
            if from_balance < transfer_data.amount:
                raise ValueError(f"Insufficient balance. Available: ${from_balance:.2f}, Required: ${transfer_data.amount:.2f}")
            
            # Verify accounts are still valid (double-check after lock acquisition)
            db.refresh(from_user)
            db.refresh(to_user)
            
            # Re-check balance after refresh
            current_from_balance = float(from_user.balance) if from_user.balance else 0.0
            if current_from_balance < transfer_data.amount:
                raise ValueError(f"Insufficient balance after verification. Available: ${current_from_balance:.2f}, Required: ${transfer_data.amount:.2f}")
            
            # Perform atomic transfer operations
            # 1. Debit from source account
            from_user.update_balance(-transfer_data.amount)
            
            # 2. Credit to destination account
            to_user.update_balance(transfer_data.amount)
            
            # 3. Create transaction record
            transaction = Transaction(
                from_account=transfer_data.from_account,
                to_account=transfer_data.to_account,
                amount=transfer_data.amount,
                transaction_type=TransactionType.TRANSFER,
                created_at=datetime.now()
            )
            
            # 4. Save all changes atomically (commit happens in atomic_operation decorator)
            db.add(transaction)
            
            # Get final balances for response
            final_from_balance = float(from_user.balance)
            final_to_balance = float(to_user.balance)
            
            logger.info(f"Transfer {transfer_id} successful: ${transfer_data.amount:.2f} from {transfer_data.from_account} to {transfer_data.to_account}")
            logger.info(f"Final balances - From: ${final_from_balance:.2f}, To: ${final_to_balance:.2f}")
            
            return TransferResponse(
                transfer_id=transfer_id,
                from_account=transfer_data.from_account,
                to_account=transfer_data.to_account,
                amount=transfer_data.amount,
                from_balance=final_from_balance,
                to_balance=final_to_balance,
                message=f"Successfully transferred ${transfer_data.amount:.2f}"
            )
            
        except ValueError as e:
            # Re-raise ValueError for business logic errors
            logger.warning(f"Transfer {transfer_id} failed - business logic error: {e}")
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Transfer {transfer_id} failed - unexpected error: {e}")
            raise ValueError(f"Failed to process transfer: {str(e)}")
        finally:
            # Always release locks
            try:
                second_lock.release()
                first_lock.release()
                logger.debug(f"Transfer {transfer_id}: Locks released")
            except Exception as e:
                logger.error(f"Error releasing locks for transfer {transfer_id}: {e}")
    
    @staticmethod
    @with_connection_retry(max_retries=2)
    def get_transfer_history(db: Session, account_number: str, limit: int = 10) -> list:
        """
        Get transfer history for an account with connection retry
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            limit (int): Maximum number of transactions to return
            
        Returns:
            list: List of transaction records
        """
        try:
            # Verify account exists
            user = db.query(User).filter_by(account_number=account_number).first()
            if not user:
                raise ValueError(f"Account {account_number} not found")
            
            # Get transactions where account is sender or receiver
            transactions = db.query(Transaction).filter(
                (Transaction.from_account == account_number) | 
                (Transaction.to_account == account_number)
            ).order_by(Transaction.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": t.id,
                    "from_account": t.from_account,
                    "to_account": t.to_account,
                    "amount": float(t.amount),
                    "transaction_type": t.transaction_type.value,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in transactions
            ]
        except Exception as e:
            logger.error(f"Error getting transfer history for account {account_number}: {e}")
            raise
    
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
    def get_concurrent_transfer_status(db: Session, account_number: str) -> dict:
        """
        Get information about concurrent transfers for an account
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            
        Returns:
            dict: Concurrent transfer information
        """
        try:
            # Check if there are any active transactions for this account
            active_transactions = db.query(Transaction).filter(
                and_(
                    (Transaction.from_account == account_number) | 
                    (Transaction.to_account == account_number),
                    Transaction.created_at >= datetime.now().replace(second=0, microsecond=0)
                )
            ).count()
            
            # Get lock status
            lock = TransferService._get_transfer_lock(account_number)
            lock_acquired = lock.locked()
            
            return {
                "account_number": account_number,
                "active_transactions_last_minute": active_transactions,
                "lock_acquired": lock_acquired,
                "lock_owner": threading.current_thread().name if lock_acquired else None
            }
        except Exception as e:
            logger.error(f"Error getting concurrent transfer status for account {account_number}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def validate_transfer_preconditions(db: Session, transfer_data: TransferRequest) -> dict:
        """
        Validate all preconditions for a transfer without executing it
        
        Args:
            db (Session): Database session
            transfer_data (TransferRequest): Transfer data
            
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
            # Check source account
            from_user = db.query(User).filter_by(account_number=transfer_data.from_account).first()
            if not from_user:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Source account {transfer_data.from_account} not found")
            else:
                from_balance = float(from_user.balance) if from_user.balance else 0.0
                validation_result["account_info"]["from_account"] = {
                    "exists": True,
                    "balance": from_balance,
                    "sufficient_funds": from_balance >= transfer_data.amount
                }
                
                if from_balance < transfer_data.amount:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Insufficient balance. Available: ${from_balance:.2f}, Required: ${transfer_data.amount:.2f}")
            
            # Check destination account
            to_user = db.query(User).filter_by(account_number=transfer_data.to_account).first()
            if not to_user:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Destination account {transfer_data.to_account} not found")
            else:
                to_balance = float(to_user.balance) if to_user.balance else 0.0
                validation_result["account_info"]["to_account"] = {
                    "exists": True,
                    "balance": to_balance
                }
            
            # Check for same account transfer
            if transfer_data.from_account == transfer_data.to_account:
                validation_result["valid"] = False
                validation_result["errors"].append("Cannot transfer to the same account")
            
            # Check for concurrent access
            from_lock = TransferService._get_transfer_lock(transfer_data.from_account)
            to_lock = TransferService._get_transfer_lock(transfer_data.to_account)
            
            if from_lock.locked():
                validation_result["warnings"].append(f"Source account {transfer_data.from_account} is currently being used in another transfer")
            
            if to_lock.locked():
                validation_result["warnings"].append(f"Destination account {transfer_data.to_account} is currently being used in another transfer")
            
            # Check database connection health
            if not TransactionManager.check_connection_health(db):
                validation_result["warnings"].append("Database connection health check failed")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result 