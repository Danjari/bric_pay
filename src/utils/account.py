import random
import string
import logging
from sqlalchemy.orm import Session
from src.models import User

logger = logging.getLogger(__name__)

def generate_account_number(db: Session, length: int = 10) -> str:
    """
    Generate a unique account number
    
    Args:
        db (Session): Database session
        length (int): Length of account number (default: 10)
        
    Returns:
        str: Unique account number
    """
    max_attempts = 100  # Prevent infinite loops
    
    for attempt in range(max_attempts):
        # Generate random account number
        account_number = ''.join(random.choices(string.digits, k=length))
        
        # Check if account number already exists
        existing_user = db.query(User).filter_by(account_number=account_number).first()
        
        if not existing_user:
            logger.info(f"Generated unique account number: {account_number}")
            return account_number
    
    # If we couldn't generate a unique number after max attempts
    raise Exception(f"Could not generate unique account number after {max_attempts} attempts")

def is_account_number_unique(db: Session, account_number: str) -> bool:
    """
    Check if an account number is unique
    
    Args:
        db (Session): Database session
        account_number (str): Account number to check
        
    Returns:
        bool: True if unique, False otherwise
    """
    existing_user = db.query(User).filter_by(account_number=account_number).first()
    return existing_user is None 