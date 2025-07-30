from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime
import uuid

from src.models import User, Transaction, TransactionType
from src.schemas import TransferRequest, TransferResponse

logger = logging.getLogger(__name__)

class TransferService:
    """Service class for transfer-related operations"""
    
    @staticmethod
    def transfer_funds(db: Session, transfer_data: TransferRequest) -> TransferResponse:
        """
        Transfer funds between accounts with atomic operations
        
        Args:
            db (Session): Database session
            transfer_data (TransferRequest): Transfer data
            
        Returns:
            TransferResponse: Transfer result with updated balances
            
        Raises:
            ValueError: If accounts not found, insufficient balance, or other validation errors
        """
        try:
            # Find both accounts
            from_user = db.query(User).filter_by(account_number=transfer_data.from_account).first()
            to_user = db.query(User).filter_by(account_number=transfer_data.to_account).first()
            
            # Validate accounts exist
            if not from_user:
                raise ValueError(f"Source account {transfer_data.from_account} not found")
            if not to_user:
                raise ValueError(f"Destination account {transfer_data.to_account} not found")
            
            # Check sufficient balance
            from_balance = float(from_user.balance) if from_user.balance else 0.0
            if from_balance < transfer_data.amount:
                raise ValueError(f"Insufficient balance. Available: ${from_balance}, Required: ${transfer_data.amount}")
            
            # Generate unique transfer ID
            transfer_id = str(uuid.uuid4())
            
            # Perform atomic transfer
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
            
            # 4. Save all changes atomically
            db.add(transaction)
            db.commit()
            db.refresh(from_user)
            db.refresh(to_user)
            
            logger.info(f"Transfer {transfer_id} successful: ${transfer_data.amount} from {transfer_data.from_account} to {transfer_data.to_account}")
            
            return TransferResponse(
                transfer_id=transfer_id,
                from_account=transfer_data.from_account,
                to_account=transfer_data.to_account,
                amount=transfer_data.amount,
                from_balance=float(from_user.balance),
                to_balance=float(to_user.balance),
                message=f"Successfully transferred ${transfer_data.amount}"
            )
            
        except ValueError as e:
            # Re-raise ValueError for business logic errors
            db.rollback()
            raise e
        except Exception as e:
            # Rollback transaction on any other error
            db.rollback()
            logger.error(f"Error processing transfer: {e}")
            raise ValueError(f"Failed to process transfer: {str(e)}")
    
    @staticmethod
    def get_transfer_history(db: Session, account_number: str, limit: int = 10) -> list:
        """
        Get transfer history for an account
        
        Args:
            db (Session): Database session
            account_number (str): Account number
            limit (int): Maximum number of transactions to return
            
        Returns:
            list: List of transaction records
        """
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
        
        return float(user.balance) if user.balance else 0.0 