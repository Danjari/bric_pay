from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import ValidationRequest, ValidationResponse, ErrorResponse
from src.utils import (
    validate_phone_number,
    validate_password_strength,
    sanitize_input,
    handle_validation_error,
    handle_generic_error,
    create_error_response
)

logger = logging.getLogger(__name__)

# Create blueprint
validation_bp = Blueprint('validation', __name__, url_prefix='/api/v1')

@validation_bp.route('/validate-field', methods=['POST'])
def validate_field():
    """
    Validate a specific field with enhanced validation rules
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        # Validate request data
        try:
            validation_request = ValidationRequest(**data)
        except ValidationError as e:
            return handle_validation_error(e)
        
        field_name = validation_request.field_name
        value = validation_request.value
        
        # Sanitize input first
        try:
            sanitized_value = sanitize_input(value)
        except Exception as e:
            return jsonify(ValidationResponse(
                field_name=field_name,
                value=value,
                is_valid=False,
                message=str(e),
                details={"type": "security_error"}
            ).dict()), 400
        
        # Validate based on field type
        validation_result = None
        
        if field_name.lower() in ['phone', 'phone_number', 'mobile']:
            is_valid = validate_phone_number(sanitized_value)
            message = "Phone number is valid" if is_valid else "Phone number format is invalid"
            details = {
                "type": "phone_validation",
                "format_required": "+[country_code][number]",
                "length_range": "10-15 digits after country code"
            }
            
        elif field_name.lower() in ['password', 'pass']:
            password_validation = validate_password_strength(sanitized_value)
            is_valid = password_validation['is_valid']
            message = "Password meets requirements" if is_valid else "Password does not meet requirements"
            details = {
                "type": "password_validation",
                "score": password_validation['score'],
                "requirements_met": password_validation['requirements_met'],
                "feedback": password_validation['feedback']
            }
            
        elif field_name.lower() in ['account_number', 'account']:
            from src.utils import validate_account_number
            is_valid = validate_account_number(sanitized_value)
            message = "Account number format is valid" if is_valid else "Account number format is invalid"
            details = {
                "type": "account_validation",
                "format_required": "8-12 digits, no leading zero"
            }
            
        elif field_name.lower() in ['name', 'surname', 'first_name', 'last_name']:
            # Basic name validation
            import re
            is_valid = bool(re.match(r'^[a-zA-Z\s\'-]{2,100}$', sanitized_value))
            message = "Name format is valid" if is_valid else "Name format is invalid"
            details = {
                "type": "name_validation",
                "allowed_chars": "letters, spaces, hyphens, apostrophes",
                "length_range": "2-100 characters"
            }
            
        elif field_name.lower() in ['amount', 'money', 'balance']:
            try:
                amount = float(sanitized_value)
                is_valid = 0.01 <= amount <= 1000000
                message = "Amount is valid" if is_valid else "Amount must be between $0.01 and $1,000,000"
                details = {
                    "type": "amount_validation",
                    "range": "0.01 - 1,000,000",
                    "currency": "USD"
                }
            except ValueError:
                is_valid = False
                message = "Amount must be a valid number"
                details = {
                    "type": "amount_validation",
                    "error": "not_a_number"
                }
                
        else:
            # Generic string validation
            is_valid = len(sanitized_value) > 0 and len(sanitized_value) <= 1000
            message = "Field is valid" if is_valid else "Field is invalid"
            details = {
                "type": "generic_validation",
                "max_length": 1000
            }
        
        return jsonify(ValidationResponse(
            field_name=field_name,
            value=sanitized_value,
            is_valid=is_valid,
            message=message,
            details=details
        ).dict()), 200
        
    except Exception as e:
        return handle_generic_error(e, "field validation")

@validation_bp.route('/validate-phone', methods=['POST'])
def validate_phone():
    """
    Validate phone number format with country code
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        phone = data.get('phone')
        if not phone:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="phone field is required"
            ).dict()), 400
        
        # Sanitize and validate
        try:
            sanitized_phone = sanitize_input(phone, max_length=20)
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Security error",
                details=str(e)
            ).dict()), 400
        
        is_valid = validate_phone_number(sanitized_phone)
        
        return jsonify({
            'phone': sanitized_phone,
            'is_valid': is_valid,
            'message': 'Phone number is valid' if is_valid else 'Phone number format is invalid',
            'requirements': {
                'format': '+[country_code][number]',
                'example': '+1234567890',
                'length': '10-15 digits after country code'
            }
        }), 200
        
    except Exception as e:
        return handle_generic_error(e, "phone validation")

@validation_bp.route('/validate-password', methods=['POST'])
def validate_password():
    """
    Validate password strength with detailed feedback
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        password = data.get('password')
        if not password:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="password field is required"
            ).dict()), 400
        
        # Sanitize and validate
        try:
            sanitized_password = sanitize_input(password, max_length=128)
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Security error",
                details=str(e)
            ).dict()), 400
        
        validation_result = validate_password_strength(sanitized_password)
        
        return jsonify({
            'password_length': len(sanitized_password),
            'is_valid': validation_result['is_valid'],
            'score': validation_result['score'],
            'strength_level': 'weak' if validation_result['score'] <= 2 else 
                            'fair' if validation_result['score'] <= 4 else 
                            'good' if validation_result['score'] <= 6 else 'strong',
            'requirements_met': validation_result['requirements_met'],
            'feedback': validation_result['feedback'],
            'message': 'Password meets requirements' if validation_result['is_valid'] else 'Password does not meet requirements'
        }), 200
        
    except Exception as e:
        return handle_generic_error(e, "password validation")

@validation_bp.route('/validate-account', methods=['POST'])
def validate_account():
    """
    Validate account number format
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        account_number = data.get('account_number')
        if not account_number:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="account_number field is required"
            ).dict()), 400
        
        # Sanitize and validate
        try:
            sanitized_account = sanitize_input(account_number, max_length=20)
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Security error",
                details=str(e)
            ).dict()), 400
        
        from src.utils import validate_account_number, get_account_number_analysis
        is_valid = validate_account_number(sanitized_account)
        analysis = get_account_number_analysis(sanitized_account)
        
        # Check uniqueness in database
        db = next(get_db())
        from src.utils import is_account_number_unique
        is_unique = is_account_number_unique(db, sanitized_account)
        
        return jsonify({
            'account_number': sanitized_account,
            'is_valid': is_valid,
            'is_unique': is_unique,
            'analysis': analysis,
            'message': 'Account number is valid' if is_valid else 'Account number format is invalid',
            'requirements': {
                'length': '8-12 digits',
                'format': 'numeric only',
                'no_leading_zero': True
            }
        }), 200
        
    except Exception as e:
        return handle_generic_error(e, "account validation")

@validation_bp.route('/validate-amount', methods=['POST'])
def validate_amount():
    """
    Validate monetary amount
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        amount = data.get('amount')
        if amount is None:
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="amount field is required"
            ).dict()), 400
        
        # Validate amount
        try:
            if isinstance(amount, str):
                amount = float(amount)
            
            is_valid = 0.01 <= amount <= 1000000
            rounded_amount = round(amount, 2)
            
            return jsonify({
                'amount': rounded_amount,
                'is_valid': is_valid,
                'message': 'Amount is valid' if is_valid else 'Amount must be between $0.01 and $1,000,000',
                'requirements': {
                    'min_amount': 0.01,
                    'max_amount': 1000000,
                    'currency': 'USD',
                    'precision': '2 decimal places'
                }
            }), 200
            
        except (ValueError, TypeError):
            return jsonify(ErrorResponse(
                error="Invalid amount",
                details="Amount must be a valid number"
            ).dict()), 400
        
    except Exception as e:
        return handle_generic_error(e, "amount validation")

@validation_bp.route('/validation-rules', methods=['GET'])
def get_validation_rules():
    """
    Get all validation rules and requirements
    """
    try:
        rules = {
            'phone_number': {
                'format': '+[country_code][number]',
                'example': '+1234567890',
                'length': '10-15 digits after country code',
                'requirements': [
                    'Must start with +',
                    'Country code cannot be all zeros',
                    'Cannot be all ones'
                ]
            },
            'password': {
                'min_length': 8,
                'recommended_length': 12,
                'requirements': [
                    'At least one lowercase letter (a-z)',
                    'At least one uppercase letter (A-Z)',
                    'At least one digit (0-9)',
                    'At least one special character (!@#$%^&*(),.?":{}|<>)'
                ],
                'avoid': [
                    'Common words (password, admin, user, etc.)',
                    'Sequential characters (123456, qwerty, etc.)',
                    'Personal information (name, birthdate, etc.)'
                ]
            },
            'account_number': {
                'length': '8-12 digits',
                'format': 'numeric only',
                'requirements': [
                    'Cannot start with zero',
                    'Must be unique in database',
                    'Cannot be reserved patterns'
                ]
            },
            'amount': {
                'range': '0.01 - 1,000,000',
                'currency': 'USD',
                'precision': '2 decimal places',
                'requirements': [
                    'Must be positive',
                    'Minimum $0.01',
                    'Maximum $1,000,000'
                ]
            },
            'name': {
                'length': '2-100 characters',
                'allowed_chars': 'letters, spaces, hyphens, apostrophes',
                'requirements': [
                    'Must be at least 2 characters',
                    'Only letters, spaces, hyphens, and apostrophes allowed'
                ]
            }
        }
        
        return jsonify({
            'validation_rules': rules,
            'message': 'Validation rules retrieved successfully'
        }), 200
        
    except Exception as e:
        return handle_generic_error(e, "validation rules retrieval") 