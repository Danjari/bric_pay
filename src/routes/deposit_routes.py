from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import DepositRequest, DepositResponse, ErrorResponse
from src.services.deposit_service import DepositService

logger = logging.getLogger(__name__)

# Create blueprint
deposit_bp = Blueprint('deposit', __name__, url_prefix='/api/v1')

@deposit_bp.route('/deposit', methods=['POST'])
def deposit_funds():
    """
    Deposit funds to a user account
    
    Expected JSON payload:
    {
        "account_number": "1234567890",
        "amount": 100.50
    }
    
    Returns:
        JSON response with updated balance and success message
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Parse and validate request data
        try:
            deposit_data = DepositRequest(**request.get_json())
        except ValidationError as e:
            logger.warning(f"Validation error in deposit request: {e}")
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Process deposit
        result = DepositService.deposit_funds(db, deposit_data)
        
        logger.info(f"Deposit successful for account {deposit_data.account_number}")
        return jsonify(result.dict()), 200
        
    except ValueError as e:
        # Handle account not found or other business logic errors
        logger.warning(f"Deposit failed: {e}")
        return jsonify(ErrorResponse(
            error="Deposit failed",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in deposit endpoint: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while processing the deposit"
        ).dict()), 500

@deposit_bp.route('/account/<account_number>/balance', methods=['GET'])
def get_balance(account_number):
    """
    Get current balance for an account
    
    Args:
        account_number (str): Account number from URL
        
    Returns:
        JSON response with current balance
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get balance
        balance = DepositService.get_account_balance(db, account_number)
        
        return jsonify({
            "account_number": account_number,
            "balance": balance,
            "message": "Balance retrieved successfully"
        }), 200
        
    except ValueError as e:
        # Handle account not found
        logger.warning(f"Balance check failed: {e}")
        return jsonify(ErrorResponse(
            error="Account not found",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in balance endpoint: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while retrieving balance"
        ).dict()), 500 