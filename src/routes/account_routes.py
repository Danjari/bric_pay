from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import CreateAccountRequest, CreateAccountResponse, ErrorResponse
from src.services.account_service import AccountService

logger = logging.getLogger(__name__)

# Create blueprint
account_bp = Blueprint('account', __name__, url_prefix='/api/v1')

@account_bp.route('/create-account', methods=['POST'])
def create_account():
    """
    Create a new user account
    
    Expected JSON payload:
    {
        "name": "John",
        "surname": "Doe", 
        "phone": "+1234567890",
        "password": "SecurePass123",
        "date_of_birth": "1990-01-01",
        "place_of_birth": "New York"
    }
    
    Returns:
        JSON response with account number and initial balance
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify(ErrorResponse(
                error="Missing request body",
                details="Request must contain JSON data"
            ).dict()), 400
        
        # Validate input data using Pydantic
        try:
            account_data = CreateAccountRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Create account using service
        result = AccountService.create_account(db, account_data)
        
        # Return success response
        return jsonify(result.dict()), 201
        
    except ValueError as e:
        # Handle business logic errors (e.g., duplicate phone number)
        logger.warning(f"Account creation failed: {e}")
        return jsonify(ErrorResponse(
            error="Account creation failed",
            details=str(e)
        ).dict()), 400
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in create_account: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while creating the account"
        ).dict()), 500
        
    finally:
        # Ensure database session is closed
        if 'db' in locals():
            db.close()

@account_bp.route('/account/<account_number>', methods=['GET'])
def get_account(account_number: str):
    """
    Get account information by account number
    
    Args:
        account_number (str): Account number to retrieve
        
    Returns:
        JSON response with account information
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get account from service
        user = AccountService.get_account_by_number(db, account_number)
        
        # Return account information (excluding sensitive data)
        return jsonify({
            "account_number": user.account_number,
            "name": user.name,
            "surname": user.surname,
            "balance": float(user.balance),
            "created_at": user.created_at.isoformat()
        }), 200
        
    except ValueError as e:
        # Handle not found errors
        logger.warning(f"Account not found: {e}")
        return jsonify(ErrorResponse(
            error="Account not found",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in get_account: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while retrieving the account"
        ).dict()), 500
        
    finally:
        # Ensure database session is closed
        if 'db' in locals():
            db.close() 