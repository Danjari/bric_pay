from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional
import re

class CreateAccountRequest(BaseModel):
    """Schema for account creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    surname: str = Field(..., min_length=1, max_length=100, description="User's last name")
    phone: str = Field(..., description="User's phone number with country code (+1234567890)")
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")
    date_of_birth: str = Field(..., description="User's date of birth (YYYY-MM-DD)")
    place_of_birth: str = Field(..., min_length=1, max_length=100, description="User's place of birth")
    
    @validator('name', 'surname')
    def validate_names(cls, v):
        """Validate name and surname format"""
        # Remove extra whitespace
        v = v.strip()
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r'^[a-zA-Z\s\'-]+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        # Check for minimum meaningful length (at least 2 characters)
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters long')
        
        return v.title()  # Capitalize properly
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format with country code"""
        # Remove any non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', v)
        
        # Check if it starts with + (country code)
        if not phone_clean.startswith('+'):
            raise ValueError('Phone number must start with country code (e.g., +1 for US, +44 for UK)')
        
        # Remove + and check digits
        digits_only = phone_clean[1:]
        
        # Check if it's a valid phone number (10-15 digits after country code)
        if not (10 <= len(digits_only) <= 15):
            raise ValueError('Phone number must be between 10 and 15 digits (excluding country code)')
        
        # Check for common invalid patterns
        if re.match(r'^\+0+', phone_clean):
            raise ValueError('Country code cannot be all zeros')
        
        if re.match(r'^\+1{10,}', phone_clean):
            raise ValueError('Phone number cannot be all ones')
        
        return phone_clean
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase letter, one lowercase letter, and one digit
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common weak patterns
        common_patterns = [
            'password', '123456', 'qwerty', 'admin', 'user',
            'letmein', 'welcome', 'monkey', 'dragon', 'master'
        ]
        
        password_lower = v.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise ValueError(f'Password cannot contain common patterns like "{pattern}"')
        
        # Check for sequential characters
        if re.search(r'(?:123|234|345|456|567|678|789|890|012)', v):
            raise ValueError('Password cannot contain sequential numbers')
        
        return v
    
    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth format and logic"""
        try:
            date_obj = datetime.strptime(v, '%Y-%m-%d')
            
            # Check if date is in the past
            if date_obj >= datetime.now():
                raise ValueError('Date of birth must be in the past')
            
            # Check if user is at least 18 years old
            age = (datetime.now() - date_obj).days / 365.25
            if age < 18:
                raise ValueError('User must be at least 18 years old')
            
            # Check if date is not too far in the past (reasonable age limit)
            if age > 120:
                raise ValueError('Date of birth seems invalid (age over 120 years)')
            
            return v
        except ValueError as e:
            if 'Date of birth must be' in str(e) or 'User must be' in str(e) or 'Date of birth seems' in str(e):
                raise e
            raise ValueError('Date of birth must be in YYYY-MM-DD format')
    
    @validator('place_of_birth')
    def validate_place_of_birth(cls, v):
        """Validate place of birth format"""
        # Remove extra whitespace
        v = v.strip()
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes, commas)
        if not re.match(r'^[a-zA-Z\s\',\-\.]+$', v):
            raise ValueError('Place of birth can only contain letters, spaces, commas, hyphens, apostrophes, and periods')
        
        # Check for minimum meaningful length
        if len(v) < 2:
            raise ValueError('Place of birth must be at least 2 characters long')
        
        return v.title()  # Capitalize properly

class CreateAccountResponse(BaseModel):
    """Schema for account creation response"""
    account_number: str = Field(..., description="Generated account number")
    balance: float = Field(..., description="Initial account balance")
    message: str = Field(..., description="Success message")

class DepositRequest(BaseModel):
    """Schema for deposit request"""
    account_number: str = Field(..., description="Account number to deposit to")
    amount: float = Field(..., gt=0, description="Amount to deposit (must be positive)")
    
    @validator('account_number')
    def validate_account_number(cls, v):
        """Validate account number format"""
        if not v.isdigit():
            raise ValueError('Account number must contain only digits')
        
        if len(v) < 8 or len(v) > 12:
            raise ValueError('Account number must be between 8 and 12 digits')
        
        if v.startswith('0'):
            raise ValueError('Account number cannot start with zero')
        
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate deposit amount"""
        if v <= 0:
            raise ValueError('Deposit amount must be positive')
        
        if v > 1000000:  # $1M limit
            raise ValueError('Deposit amount cannot exceed $1,000,000')
        
        # Check for reasonable minimum amount
        if v < 0.01:
            raise ValueError('Deposit amount must be at least $0.01')
        
        return round(v, 2)  # Round to 2 decimal places

class DepositResponse(BaseModel):
    """Schema for deposit response"""
    account_number: str = Field(..., description="Account number")
    new_balance: float = Field(..., description="Updated account balance")
    deposited_amount: float = Field(..., description="Amount that was deposited")
    message: str = Field(..., description="Success message")

class TransferRequest(BaseModel):
    """Schema for transfer request"""
    from_account: str = Field(..., description="Source account number")
    to_account: str = Field(..., description="Destination account number")
    amount: float = Field(..., gt=0, description="Amount to transfer (must be positive)")
    
    @validator('from_account', 'to_account')
    def validate_account_numbers(cls, v):
        """Validate account number format"""
        if not v.isdigit():
            raise ValueError('Account number must contain only digits')
        
        if len(v) < 8 or len(v) > 12:
            raise ValueError('Account number must be between 8 and 12 digits')
        
        if v.startswith('0'):
            raise ValueError('Account number cannot start with zero')
        
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate transfer amount"""
        if v <= 0:
            raise ValueError('Transfer amount must be positive')
        
        if v > 1000000:  # $1M limit
            raise ValueError('Transfer amount cannot exceed $1,000,000')
        
        # Check for reasonable minimum amount
        if v < 0.01:
            raise ValueError('Transfer amount must be at least $0.01')
        
        return round(v, 2)  # Round to 2 decimal places
    
    @validator('to_account')
    def validate_different_accounts(cls, v, values):
        """Validate that from_account and to_account are different"""
        if 'from_account' in values and v == values['from_account']:
            raise ValueError('Cannot transfer to the same account')
        return v

class TransferResponse(BaseModel):
    """Schema for transfer response"""
    transfer_id: str = Field(..., description="Unique transfer ID")
    from_account: str = Field(..., description="Source account number")
    to_account: str = Field(..., description="Destination account number")
    amount: float = Field(..., description="Amount transferred")
    from_balance: float = Field(..., description="Updated balance of source account")
    to_balance: float = Field(..., description="Updated balance of destination account")
    message: str = Field(..., description="Success message")

class ValidationRequest(BaseModel):
    """Schema for validation requests"""
    field_name: str = Field(..., description="Field name to validate")
    value: str = Field(..., description="Value to validate")

class ValidationResponse(BaseModel):
    """Schema for validation responses"""
    field_name: str = Field(..., description="Field name that was validated")
    value: str = Field(..., description="Value that was validated")
    is_valid: bool = Field(..., description="Whether the value is valid")
    message: str = Field(..., description="Validation message")
    details: Optional[dict] = Field(None, description="Additional validation details")

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    field: Optional[str] = Field(None, description="Field that caused the error")
    code: Optional[str] = Field(None, description="Error code for programmatic handling") 