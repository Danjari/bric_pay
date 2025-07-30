from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging

from src.database import get_db
from src.schemas import TransferRequest, TransferResponse, ErrorResponse
from src.services.transfer_service import TransferService

logger = logging.getLogger(__name__)

# Create blueprint
transfer_bp = Blueprint('transfer', __name__, url_prefix='/api/v1')

@transfer_bp.route('/transfer', methods=['POST'])
def transfer_funds():
    """
    Transfer funds between accounts
    
    Expected JSON payload:
    {
        "from_account": "1234567890",
        "to_account": "0987654321",
        "amount": 100.50
    }
    
    Returns:
        JSON response with transfer confirmation and updated balances
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Parse and validate request data
        try:
            transfer_data = TransferRequest(**request.get_json())
        except ValidationError as e:
            logger.warning(f"Validation error in transfer request: {e}")
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Process transfer
        result = TransferService.transfer_funds(db, transfer_data)
        
        logger.info(f"Transfer successful: {result.transfer_id}")
        return jsonify(result.dict()), 200
        
    except ValueError as e:
        # Handle business logic errors
        logger.warning(f"Transfer failed: {e}")
        return jsonify(ErrorResponse(
            error="Transfer failed",
            details=str(e)
        ).dict()), 400
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in transfer endpoint: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while processing the transfer"
        ).dict()), 500

@transfer_bp.route('/account/<account_number>/transactions', methods=['GET'])
def get_transaction_history(account_number):
    """
    Get transaction history for an account
    
    Args:
        account_number (str): Account number from URL
        
    Query Parameters:
        limit (int): Maximum number of transactions to return (default: 10)
        
    Returns:
        JSON response with transaction history
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        if limit > 100:  # Cap at 100 transactions
            limit = 100
        
        # Get transaction history
        transactions = TransferService.get_transfer_history(db, account_number, limit)
        
        return jsonify({
            "account_number": account_number,
            "transactions": transactions,
            "count": len(transactions),
            "message": "Transaction history retrieved successfully"
        }), 200
        
    except ValueError as e:
        # Handle account not found
        logger.warning(f"Transaction history failed: {e}")
        return jsonify(ErrorResponse(
            error="Account not found",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in transaction history endpoint: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred while retrieving transaction history"
        ).dict()), 500

@transfer_bp.route('/account/<account_number>/balance', methods=['GET'])
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
        balance = TransferService.get_account_balance(db, account_number)
        
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