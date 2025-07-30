from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.models import User
from src.schemas import CreateAccountRequest, CreateAccountResponse
from src.utils.auth import hash_password
from src.utils.account import generate_account_number

logger = logging.getLogger(__name__)

class AccountService:
    """Service class for account-related operations"""
    
    @staticmethod
    def create_account(db: Session, account_data: CreateAccountRequest) -> CreateAccountResponse:
        """
        Create a new user account
        
        Args:
            db (Session): Database session
            account_data (CreateAccountRequest): Account creation data
            
        Returns:
            CreateAccountResponse: Created account information
            
        Raises:
            ValueError: If phone number already exists
            Exception: If account creation fails
        """
        try:
            # Check if phone number already exists
            existing_user = db.query(User).filter_by(phone=account_data.phone).first()
            if existing_user:
                raise ValueError(f"Phone number {account_data.phone} is already registered")
            
            # Hash the password
            hashed_password = hash_password(account_data.password)
            
            # Generate unique account number
            account_number = generate_account_number(db)
            
            # Parse date of birth
            date_of_birth = datetime.strptime(account_data.date_of_birth, '%Y-%m-%d')
            
            # Create new user
            new_user = User(
                name=account_data.name,
                surname=account_data.surname,
                phone=account_data.phone,
                password_hash=hashed_password,
                date_of_birth=date_of_birth,
                place_of_birth=account_data.place_of_birth,
                account_number=account_number,
                balance=0.00  # Initial balance is 0
            )
            
            # Add to database
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"Created new account: {account_number} for user {account_data.name} {account_data.surname}")
            
            return CreateAccountResponse(
                account_number=account_number,
                balance=0.00,
                message="Account created successfully"
            )
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error while creating account: {e}")
            raise ValueError("Account creation failed due to database constraint violation")
            
        except ValueError as e:
            db.rollback()
            logger.error(f"Validation error while creating account: {e}")
            raise e
            
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while creating account: {e}")
            raise Exception(f"Failed to create account: {str(e)}")
    
    @staticmethod
    def get_account_by_number(db: Session, account_number: str) -> User:
        """
        Get user account by account number
        
        Args:
            db (Session): Database session
            account_number (str): Account number to search for
            
        Returns:
            User: User object if found
            
        Raises:
            ValueError: If account not found
        """
        user = db.query(User).filter_by(account_number=account_number).first()
        if not user:
            raise ValueError(f"Account number {account_number} not found")
        return user
    
    @staticmethod
    def get_account_by_phone(db: Session, phone: str) -> User:
        """
        Get user account by phone number
        
        Args:
            db (Session): Database session
            phone (str): Phone number to search for
            
        Returns:
            User: User object if found
            
        Raises:
            ValueError: If account not found
        """
        user = db.query(User).filter_by(phone=phone).first()
        if not user:
            raise ValueError(f"Phone number {phone} not found")
        return user 