from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import DepositRequest, DepositResponse, ErrorResponse
from src.services.deposit_service import DepositService
from src.utils import (
    handle_validation_error,
    handle_business_logic_error,
    handle_generic_error,
    sanitize_input,
    BusinessLogicError
)

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
            return handle_validation_error(e)
        
        # Process deposit
        result = DepositService.deposit_funds(db, deposit_data)
        
        logger.info(f"Deposit successful for account {deposit_data.account_number}")
        return jsonify(result.dict()), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "deposit operation")

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
        
        # Get balance
        balance = DepositService.get_account_balance(db, sanitized_account)
        
        return jsonify({
            "account_number": sanitized_account,
            "balance": balance,
            "message": "Balance retrieved successfully"
        }), 200
        
    except BusinessLogicError as e:
        return handle_business_logic_error(e)
        
    except Exception as e:
        return handle_generic_error(e, "balance retrieval") 