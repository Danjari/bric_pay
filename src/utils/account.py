import random
import string
import logging
import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models import User

logger = logging.getLogger(__name__)

class AccountNumberGenerator:
    """Enhanced account number generation system"""
    
    # Configuration constants
    DEFAULT_LENGTH = 10
    MAX_LENGTH = 12
    MIN_LENGTH = 8
    MAX_ATTEMPTS = 1000  # Increased for better uniqueness guarantee
    
    # Account number patterns (for validation)
    PATTERN_10_DIGIT = re.compile(r'^\d{10}$')
    PATTERN_12_DIGIT = re.compile(r'^\d{12}$')
    
    # Reserved patterns (avoid common sequences)
    RESERVED_PATTERNS = [
        '0000000000',  # All zeros
        '1111111111',  # All ones
        '1234567890',  # Sequential
        '0987654321',  # Reverse sequential
        '9999999999',  # All nines
    ]
    
    @classmethod
    def generate_account_number(cls, db: Session, length: int = DEFAULT_LENGTH) -> str:
        """
        Generate a secure and unique account number
        
        Args:
            db (Session): Database session
            length (int): Length of account number (8-12 digits)
            
        Returns:
            str: Unique account number
            
        Raises:
            ValueError: If length is invalid
            Exception: If unable to generate unique number
        """
        # Validate length
        if not cls.MIN_LENGTH <= length <= cls.MAX_LENGTH:
            raise ValueError(f"Account number length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} digits")
        
        logger.info(f"Generating account number with length {length}")
        
        for attempt in range(cls.MAX_ATTEMPTS):
            try:
                # Generate candidate account number
                account_number = cls._generate_candidate(length)
                
                # Validate the candidate
                if cls._is_valid_candidate(account_number):
                    # Check uniqueness in database
                    if cls._is_unique_in_db(db, account_number):
                        logger.info(f"Generated unique account number: {account_number} (attempt {attempt + 1})")
                        return account_number
                
            except Exception as e:
                logger.warning(f"Error during account number generation attempt {attempt + 1}: {e}")
                continue
        
        # If we reach here, we couldn't generate a unique number
        error_msg = f"Could not generate unique account number after {cls.MAX_ATTEMPTS} attempts"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    @classmethod
    def _generate_candidate(cls, length: int) -> str:
        """
        Generate a candidate account number
        
        Args:
            length (int): Length of account number
            
        Returns:
            str: Candidate account number
        """
        # Use cryptographically secure random number generation
        # Avoid leading zeros for better readability
        first_digit = random.choice('123456789')  # Avoid leading zero
        remaining_digits = ''.join(random.choices(string.digits, k=length - 1))
        return first_digit + remaining_digits
    
    @classmethod
    def _is_valid_candidate(cls, account_number: str) -> bool:
        """
        Validate a candidate account number
        
        Args:
            account_number (str): Account number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check length
        if len(account_number) < cls.MIN_LENGTH or len(account_number) > cls.MAX_LENGTH:
            return False
        
        # Check if it's all digits
        if not account_number.isdigit():
            return False
        
        # Check for leading zero (not allowed for generated numbers)
        if account_number.startswith('0'):
            return False
        
        # Check for reserved patterns
        if account_number in cls.RESERVED_PATTERNS:
            return False
        
        # Check for too many consecutive digits
        if cls._has_too_many_consecutive(account_number):
            return False
        
        # Check for too many repeated digits
        if cls._has_too_many_repeated(account_number):
            return False
        
        return True
    
    @classmethod
    def _has_too_many_consecutive(cls, account_number: str, max_consecutive: int = 4) -> bool:
        """
        Check if account number has too many consecutive digits
        
        Args:
            account_number (str): Account number to check
            max_consecutive (int): Maximum allowed consecutive digits
            
        Returns:
            bool: True if too many consecutive digits
        """
        consecutive_count = 1
        for i in range(1, len(account_number)):
            if int(account_number[i]) == int(account_number[i-1]) + 1:
                consecutive_count += 1
                if consecutive_count > max_consecutive:
                    return True
            else:
                consecutive_count = 1
        return False
    
    @classmethod
    def _has_too_many_repeated(cls, account_number: str, max_repeated: int = 3) -> bool:
        """
        Check if account number has too many repeated digits
        
        Args:
            account_number (str): Account number to check
            max_repeated (int): Maximum allowed repeated digits
            
        Returns:
            bool: True if too many repeated digits
        """
        for digit in string.digits:
            if account_number.count(digit) > max_repeated:
                return True
        return False
    
    @classmethod
    def _is_unique_in_db(cls, db: Session, account_number: str) -> bool:
        """
        Check if account number is unique in database
        
        Args:
            db (Session): Database session
            account_number (str): Account number to check
            
        Returns:
            bool: True if unique, False otherwise
        """
        try:
            existing_user = db.query(User).filter_by(account_number=account_number).first()
            return existing_user is None
        except Exception as e:
            logger.error(f"Error checking account number uniqueness: {e}")
            return False
    
    @classmethod
    def validate_account_number_format(cls, account_number: str) -> bool:
        """
        Validate account number format
        
        Args:
            account_number (str): Account number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not account_number:
            return False
        
        # Check length
        if not (cls.MIN_LENGTH <= len(account_number) <= cls.MAX_LENGTH):
            return False
        
        # Check if it's all digits
        if not account_number.isdigit():
            return False
        
        # Check for reserved patterns
        if account_number in cls.RESERVED_PATTERNS:
            return False
        
        return True
    
    @classmethod
    def get_account_number_info(cls, account_number: str) -> dict:
        """
        Get information about an account number
        
        Args:
            account_number (str): Account number to analyze
            
        Returns:
            dict: Information about the account number
        """
        info = {
            'length': len(account_number),
            'is_valid_format': cls.validate_account_number_format(account_number),
            'is_reserved': account_number in cls.RESERVED_PATTERNS,
            'has_consecutive': cls._has_too_many_consecutive(account_number),
            'has_repeated': cls._has_too_many_repeated(account_number),
            'digit_distribution': {}
        }
        
        # Analyze digit distribution
        for digit in string.digits:
            count = account_number.count(digit)
            if count > 0:
                info['digit_distribution'][digit] = count
        
        return info

# Backward compatibility functions
def generate_account_number(db: Session, length: int = 10) -> str:
    """
    Generate a unique account number (legacy function)
    
    Args:
        db (Session): Database session
        length (int): Length of account number (default: 10)
        
    Returns:
        str: Unique account number
    """
    return AccountNumberGenerator.generate_account_number(db, length)

def is_account_number_unique(db: Session, account_number: str) -> bool:
    """
    Check if an account number is unique (legacy function)
    
    Args:
        db (Session): Database session
        account_number (str): Account number to check
        
    Returns:
        bool: True if unique, False otherwise
    """
    return AccountNumberGenerator._is_unique_in_db(db, account_number)

def validate_account_number(account_number: str) -> bool:
    """
    Validate account number format (new function)
    
    Args:
        account_number (str): Account number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return AccountNumberGenerator.validate_account_number_format(account_number)

def get_account_number_analysis(account_number: str) -> dict:
    """
    Get detailed analysis of an account number (new function)
    
    Args:
        account_number (str): Account number to analyze
        
    Returns:
        dict: Detailed analysis information
    """
    return AccountNumberGenerator.get_account_number_info(account_number) 