from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime

from src.models import User, Transaction, TransactionType
from src.schemas import DepositRequest, DepositResponse

logger = logging.getLogger(__name__)

class DepositService:
    """Service class for deposit-related operations"""
    
    @staticmethod
    def deposit_funds(db: Session, deposit_data: DepositRequest) -> DepositResponse:
        """
        Deposit funds to a user account
        
        Args:
            db (Session): Database session
            deposit_data (DepositRequest): Deposit data
            
        Returns:
            DepositResponse: Deposit result with updated balance
            
        Raises:
            ValueError: If account not found or invalid amount
        """
        try:
            # Find the user account
            user = db.query(User).filter_by(account_number=deposit_data.account_number).first()
            
            if not user:
                raise ValueError(f"Account {deposit_data.account_number} not found")
            
            # Update account balance
            old_balance = user.balance
            user.update_balance(deposit_data.amount)
            
            # Create transaction record
            transaction = Transaction(
                from_account=None,  # Deposits don't have a source account
                to_account=deposit_data.account_number,
                amount=deposit_data.amount,
                transaction_type=TransactionType.DEPOSIT,
                created_at=datetime.now()
            )
            
            # Save changes to database
            db.add(transaction)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Deposit of ${deposit_data.amount} successful for account {deposit_data.account_number}")
            
            return DepositResponse(
                account_number=deposit_data.account_number,
                new_balance=user.balance,
                deposited_amount=deposit_data.amount,
                message=f"Successfully deposited ${deposit_data.amount}"
            )
            
        except ValueError as e:
            # Re-raise ValueError for account not found
            raise e
        except Exception as e:
            # Rollback transaction on error
            db.rollback()
            logger.error(f"Error depositing funds: {e}")
            raise ValueError(f"Failed to process deposit: {str(e)}")
    
    @staticmethod
    def get_account_balance(db: Session, account_number: str) -> float:
        """
        Get current balance for an account
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            
        Returns:
            float: Current balance
            
        Raises:
            ValueError: If account not found
        """
        user = db.query(User).filter_by(account_number=account_number).first()
        
        if not user:
            raise ValueError(f"Account {account_number} not found")
        
        return user.balance 