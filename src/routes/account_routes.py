from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import CreateAccountRequest, CreateAccountResponse, ErrorResponse
from src.services.account_service import AccountService
from src.utils import validate_account_number, get_account_number_analysis

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
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Request body is required"
            ).dict()), 400
        
        # Validate request data
        try:
            account_data = CreateAccountRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Get database session
        db = next(get_db())
        
        # Create account
        result = AccountService.create_account(db, account_data)
        
        return jsonify(result.dict()), 201
        
    except ValueError as e:
        logger.error(f"Validation error while creating account: {e}")
        return jsonify(ErrorResponse(
            error="Validation error",
            details=str(e)
        ).dict()), 400
        
    except Exception as e:
        logger.error(f"Unexpected error while creating account: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to create account"
        ).dict()), 500

@account_bp.route('/account/<account_number>', methods=['GET'])
def get_account(account_number):
    """
    Get account information by account number
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get account
        user = AccountService.get_account_by_number(db, account_number)
        
        return jsonify(user.to_dict()), 200
        
    except ValueError as e:
        logger.error(f"Account not found: {e}")
        return jsonify(ErrorResponse(
            error="Account not found",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        logger.error(f"Unexpected error while getting account: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to get account"
        ).dict()), 500

@account_bp.route('/validate-account-number', methods=['POST'])
def validate_account_number_endpoint():
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
        
        # Validate account number format
        is_valid = validate_account_number(account_number)
        
        return jsonify({
            'account_number': account_number,
            'is_valid': is_valid,
            'message': 'Account number is valid' if is_valid else 'Account number format is invalid'
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating account number: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to validate account number"
        ).dict()), 500

@account_bp.route('/analyze-account-number', methods=['POST'])
def analyze_account_number_endpoint():
    """
    Get detailed analysis of an account number
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
        
        # Get database session for uniqueness check
        db = next(get_db())
        
        # Analyze account number
        analysis = get_account_number_analysis(account_number)
        
        # Add uniqueness check
        from src.utils import is_account_number_unique
        analysis['is_unique_in_db'] = is_account_number_unique(db, account_number)
        
        return jsonify({
            'account_number': account_number,
            'analysis': analysis,
            'message': 'Account number analysis completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing account number: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to analyze account number"
        ).dict()), 500

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
            return jsonify(ErrorResponse(
                error="Invalid request",
                details="Length must be an integer between 8 and 12"
            ).dict()), 400
        
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
        
    except Exception as e:
        logger.error(f"Error generating account number: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to generate account number"
        ).dict()), 500 