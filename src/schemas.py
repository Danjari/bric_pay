from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional
import re

class CreateAccountRequest(BaseModel):
    """Schema for account creation request"""
    name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    surname: str = Field(..., min_length=1, max_length=100, description="User's last name")
    phone: str = Field(..., description="User's phone number")
    password: str = Field(..., min_length=8, description="User's password (min 8 characters)")
    date_of_birth: str = Field(..., description="User's date of birth (YYYY-MM-DD)")
    place_of_birth: str = Field(..., min_length=1, max_length=100, description="User's place of birth")
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Remove any non-digit characters
        phone_clean = re.sub(r'\D', '', v)
        
        # Check if it's a valid phone number (10-15 digits)
        if not (10 <= len(phone_clean) <= 15):
            raise ValueError('Phone number must be between 10 and 15 digits')
        
        return v
    
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
            
            return v
        except ValueError as e:
            if 'Date of birth must be' in str(e):
                raise e
            raise ValueError('Date of birth must be in YYYY-MM-DD format')

class CreateAccountResponse(BaseModel):
    """Schema for account creation response"""
    account_number: str = Field(..., description="Generated account number")
    balance: float = Field(..., description="Initial account balance")
    message: str = Field(..., description="Success message")
    
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details") 