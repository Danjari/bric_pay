"""
Error Handling Utilities
Provides centralized error handling and consistent error responses
"""
import logging
from typing import Dict, Any, Optional, Union
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from flask import jsonify

logger = logging.getLogger(__name__)

class ValidationErrorHandler:
    """Handles validation errors and provides detailed feedback"""
    
    @staticmethod
    def format_validation_error(error: ValidationError) -> Dict[str, Any]:
        """
        Format Pydantic validation error into a structured response
        
        Args:
            error (ValidationError): Pydantic validation error
            
        Returns:
            dict: Formatted error response
        """
        errors = []
        
        for error_detail in error.errors():
            field = error_detail.get('loc', ['unknown'])[-1] if error_detail.get('loc') else 'unknown'
            message = error_detail.get('msg', 'Validation error')
            error_type = error_detail.get('type', 'value_error')
            
            errors.append({
                'field': field,
                'message': message,
                'type': error_type,
                'value': error_detail.get('input', 'N/A')
            })
        
        return {
            'error': 'Validation error',
            'details': 'One or more fields failed validation',
            'code': 'VALIDATION_ERROR',
            'field_errors': errors,
            'total_errors': len(errors)
        }

class BusinessLogicError(Exception):
    """Custom exception for business logic errors"""
    
    def __init__(self, message: str, code: str = None, field: str = None, status_code: int = 400):
        self.message = message
        self.code = code or 'BUSINESS_LOGIC_ERROR'
        self.field = field
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        self.message = message
        self.code = code or 'DATABASE_ERROR'
        self.status_code = status_code
        super().__init__(self.message)

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    
    def __init__(self, message: str, code: str = None, status_code: int = 403):
        self.message = message
        self.code = code or 'SECURITY_ERROR'
        self.status_code = status_code
        super().__init__(self.message)

def handle_validation_error(error: ValidationError) -> tuple:
    """
    Handle Pydantic validation errors
    
    Args:
        error (ValidationError): Pydantic validation error
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    formatted_error = ValidationErrorHandler.format_validation_error(error)
    logger.warning(f"Validation error: {formatted_error}")
    return jsonify(formatted_error), 400

def handle_business_logic_error(error: BusinessLogicError) -> tuple:
    """
    Handle business logic errors
    
    Args:
        error (BusinessLogicError): Business logic error
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    error_response = {
        'error': error.message,
        'code': error.code,
        'field': error.field
    }
    logger.warning(f"Business logic error: {error_response}")
    return jsonify(error_response), error.status_code

def handle_database_error(error: Union[DatabaseError, IntegrityError, OperationalError]) -> tuple:
    """
    Handle database errors
    
    Args:
        error: Database error
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    if isinstance(error, DatabaseError):
        error_response = {
            'error': error.message,
            'code': error.code,
            'details': 'Database operation failed'
        }
        status_code = error.status_code
    elif isinstance(error, IntegrityError):
        error_response = {
            'error': 'Data integrity error',
            'code': 'INTEGRITY_ERROR',
            'details': 'The requested operation would violate data integrity constraints'
        }
        status_code = 409
    elif isinstance(error, OperationalError):
        error_response = {
            'error': 'Database operation error',
            'code': 'OPERATIONAL_ERROR',
            'details': 'Database operation failed due to a system error'
        }
        status_code = 503
    else:
        error_response = {
            'error': 'Database error',
            'code': 'DATABASE_ERROR',
            'details': 'An unexpected database error occurred'
        }
        status_code = 500
    
    logger.error(f"Database error: {error_response}")
    return jsonify(error_response), status_code

def handle_security_error(error: SecurityError) -> tuple:
    """
    Handle security-related errors
    
    Args:
        error (SecurityError): Security error
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    error_response = {
        'error': error.message,
        'code': error.code,
        'details': 'Security validation failed'
    }
    logger.warning(f"Security error: {error_response}")
    return jsonify(error_response), error.status_code

def handle_generic_error(error: Exception, context: str = "Unknown operation") -> tuple:
    """
    Handle generic/unexpected errors
    
    Args:
        error (Exception): Generic error
        context (str): Context where the error occurred
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    error_response = {
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR',
        'details': f'An unexpected error occurred during {context}'
    }
    logger.error(f"Unexpected error during {context}: {str(error)}", exc_info=True)
    return jsonify(error_response), 500

def create_error_response(
    message: str,
    code: str = None,
    field: str = None,
    details: str = None,
    status_code: int = 400
) -> tuple:
    """
    Create a standardized error response
    
    Args:
        message (str): Error message
        code (str): Error code
        field (str): Field that caused the error
        details (str): Additional details
        status_code (int): HTTP status code
        
    Returns:
        tuple: Flask response tuple (json, status_code)
    """
    error_response = {
        'error': message,
        'code': code or 'GENERIC_ERROR'
    }
    
    if field:
        error_response['field'] = field
    
    if details:
        error_response['details'] = details
    
    logger.warning(f"Error response: {error_response}")
    return jsonify(error_response), status_code

def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize input string to prevent injection attacks
    
    Args:
        value (str): Input value to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized value
        
    Raises:
        SecurityError: If input is potentially dangerous
    """
    if not isinstance(value, str):
        raise SecurityError("Input must be a string", "INVALID_INPUT_TYPE")
    
    # Check length
    if len(value) > max_length:
        raise SecurityError(f"Input too long (max {max_length} characters)", "INPUT_TOO_LONG")
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        '<script', 'javascript:', 'data:', 'vbscript:', 'onload=',
        'onerror=', 'onclick=', 'eval(', 'document.cookie'
    ]
    
    sanitized_lower = sanitized.lower()
    for pattern in dangerous_patterns:
        if pattern in sanitized_lower:
            raise SecurityError(f"Input contains potentially dangerous content: {pattern}", "DANGEROUS_INPUT")
    
    return sanitized.strip()

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format with enhanced checks
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    
    # Remove any non-digit characters except +
    phone_clean = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with + (country code)
    if not phone_clean.startswith('+'):
        return False
    
    # Remove + and check digits
    digits_only = phone_clean[1:]
    
    # Check if it's a valid phone number (10-15 digits after country code)
    if not (10 <= len(digits_only) <= 15):
        return False
    
    # Check for common invalid patterns
    if re.match(r'^\+0+', phone_clean):
        return False
    
    if re.match(r'^\+1{10,}', phone_clean):
        return False
    
    return True

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Enhanced password strength validation
    
    Args:
        password (str): Password to validate
        
    Returns:
        dict: Validation result with details
    """
    import re
    
    result = {
        'is_valid': True,
        'score': 0,
        'feedback': [],
        'requirements_met': {
            'length': False,
            'uppercase': False,
            'lowercase': False,
            'digit': False,
            'special': False
        }
    }
    
    # Length check
    if len(password) >= 8:
        result['requirements_met']['length'] = True
        result['score'] += 1
    else:
        result['feedback'].append("Password must be at least 8 characters long")
        result['is_valid'] = False
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        result['requirements_met']['lowercase'] = True
        result['score'] += 1
    else:
        result['feedback'].append("Password must contain at least one lowercase letter")
        result['is_valid'] = False
    
    if re.search(r'[A-Z]', password):
        result['requirements_met']['uppercase'] = True
        result['score'] += 1
    else:
        result['feedback'].append("Password must contain at least one uppercase letter")
        result['is_valid'] = False
    
    if re.search(r'\d', password):
        result['requirements_met']['digit'] = True
        result['score'] += 1
    else:
        result['feedback'].append("Password must contain at least one digit")
        result['is_valid'] = False
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['requirements_met']['special'] = True
        result['score'] += 1
    else:
        result['feedback'].append("Password must contain at least one special character")
        result['is_valid'] = False
    
    # Check for common weak patterns
    common_patterns = [
        'password', '123456', 'qwerty', 'admin', 'user',
        'letmein', 'welcome', 'monkey', 'dragon', 'master'
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            result['feedback'].append(f"Avoid common patterns like '{pattern}'")
            result['score'] -= 1
            break
    
    # Check for sequential characters
    if re.search(r'(?:123|234|345|456|567|678|789|890|012)', password):
        result['feedback'].append("Avoid sequential numbers")
        result['score'] -= 1
    
    return result 