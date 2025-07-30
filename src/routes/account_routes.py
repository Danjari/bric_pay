from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import CreateAccountRequest, CreateAccountResponse, ErrorResponse
from src.services.account_service import AccountService
from src.utils import (
    validate_account_number, 
    get_account_number_analysis,
    handle_validation_error,
    handle_business_logic_error,
    handle_generic_error,
    sanitize_input,
    BusinessLogicError
)

logger = logging.getLogger(__name__)

# Create blueprint
account_bp = Blueprint('account', __name__, url_prefix='/api/v1')

@account_bp.route('/create-account', methods=['POST'])
def create_account():
    """
    Create a new user account
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            raise BusinessLogicError(
                "Invalid request",
                code="MISSING_REQUEST_BODY",
                details="Request body is required"
            )
        
        # Validate request data
        try:
            account_data = CreateAccountRequest(**data)
        except ValidationError as e:
            return handle_validation_error(e)
        
        # Get database session
        db = next(get_db())
        
        # Create account
        result = AccountService.create_account(db, account_data)
        
        return jsonify(result.dict()), 201
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "account creation")

@account_bp.route('/account/<account_number>', methods=['GET'])
def get_account(account_number):
    """
    Get account information by account number
    """
    try:
        # Sanitize account number
        try:
            sanitized_account = sanitize_input(account_number, max_length=20)
        except Exception as e:
            raise BusinessLogicError(
                str(e),
                code="INVALID_ACCOUNT_NUMBER",
                field="account_number"
            )
        
        # Get database session
        db = next(get_db())
        
        # Get account
        user = AccountService.get_account_by_number(db, sanitized_account)
        
        return jsonify(user.to_dict()), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "account retrieval")

@account_bp.route('/validate-account-number', methods=['POST'])
def validate_account_number_endpoint():
    """
    Validate account number format
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            raise BusinessLogicError(
                "Invalid request",
                code="MISSING_REQUEST_BODY",
                details="Request body is required"
            )
        
        account_number = data.get('account_number')
        if not account_number:
            raise BusinessLogicError(
                "Invalid request",
                code="MISSING_FIELD",
                field="account_number",
                details="account_number field is required"
            )
        
        # Sanitize account number
        try:
            sanitized_account = sanitize_input(account_number, max_length=20)
        except Exception as e:
            raise BusinessLogicError(
                str(e),
                code="INVALID_ACCOUNT_NUMBER",
                field="account_number"
            )
        
        # Validate account number format
        is_valid = validate_account_number(sanitized_account)
        
        return jsonify({
            'account_number': sanitized_account,
            'is_valid': is_valid,
            'message': 'Account number is valid' if is_valid else 'Account number format is invalid'
        }), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "account number validation")

@account_bp.route('/analyze-account-number', methods=['POST'])
def analyze_account_number_endpoint():
    """
    Get detailed analysis of an account number
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            raise BusinessLogicError(
                "Invalid request",
                code="MISSING_REQUEST_BODY",
                details="Request body is required"
            )
        
        account_number = data.get('account_number')
        if not account_number:
            raise BusinessLogicError(
                "Invalid request",
                code="MISSING_FIELD",
                field="account_number",
                details="account_number field is required"
            )
        
        # Sanitize account number
        try:
            sanitized_account = sanitize_input(account_number, max_length=20)
        except Exception as e:
            raise BusinessLogicError(
                str(e),
                code="INVALID_ACCOUNT_NUMBER",
                field="account_number"
            )
        
        # Get database session for uniqueness check
        db = next(get_db())
        
        # Analyze account number
        analysis = get_account_number_analysis(sanitized_account)
        
        # Add uniqueness check
        from src.utils import is_account_number_unique
        analysis['is_unique_in_db'] = is_account_number_unique(db, sanitized_account)
        
        return jsonify({
            'account_number': sanitized_account,
            'analysis': analysis,
            'message': 'Account number analysis completed'
        }), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "account number analysis")

@account_bp.route('/generate-account-number', methods=['POST'])
def generate_account_number_endpoint():
    """
    Generate a new account number (for testing/development)
    """
    try:
        # Get JSON data from request
        data = request.get_json() or {}
        length = data.get('length', 10)
        
        # Validate length
        if not isinstance(length, int) or length < 8 or length > 12:
            raise BusinessLogicError(
                "Invalid length parameter",
                code="INVALID_LENGTH",
                field="length",
                details="Length must be an integer between 8 and 12"
            )
        
        # Get database session
        db = next(get_db())
        
        # Generate account number
        from src.utils import generate_account_number
        account_number = generate_account_number(db, length)
        
        return jsonify({
            'account_number': account_number,
            'length': length,
            'message': 'Account number generated successfully'
        }), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "account number generation") 