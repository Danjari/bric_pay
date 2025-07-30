from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import logging
from datetime import datetime

from src.database import get_db
from src.schemas import TransferRequest, TransferResponse, ErrorResponse
from src.services.transfer_service import TransferService
from src.utils import TransactionManager

logger = logging.getLogger(__name__)

# Create blueprint
transfer_bp = Blueprint('transfer', __name__, url_prefix='/api/v1')

@transfer_bp.route('/transfer', methods=['POST'])
def transfer_funds():
    """
    Transfer funds between accounts
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
            transfer_data = TransferRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Get database session
        db = next(get_db())
        
        # Perform transfer
        result = TransferService.transfer_funds(db, transfer_data)
        
        return jsonify(result.dict()), 200
        
    except ValueError as e:
        logger.error(f"Transfer failed: {e}")
        return jsonify(ErrorResponse(
            error="Transfer failed",
            details=str(e)
        ).dict()), 400
        
    except Exception as e:
        logger.error(f"Unexpected error during transfer: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to process transfer"
        ).dict()), 500

@transfer_bp.route('/account/<account_number>/transactions', methods=['GET'])
def get_transaction_history(account_number):
    """
    Get transaction history for an account
    """
    try:
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        if limit > 100:  # Prevent excessive queries
            limit = 100
        
        # Get database session
        db = next(get_db())
        
        # Get transaction history
        transactions = TransferService.get_transfer_history(db, account_number, limit)
        
        return jsonify({
            "account_number": account_number,
            "transactions": transactions,
            "count": len(transactions),
            "limit": limit
        }), 200
        
    except ValueError as e:
        logger.error(f"Failed to get transaction history: {e}")
        return jsonify(ErrorResponse(
            error="Failed to get transaction history",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        logger.error(f"Unexpected error getting transaction history: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to get transaction history"
        ).dict()), 500

@transfer_bp.route('/account/<account_number>/balance', methods=['GET'])
def get_balance(account_number):
    """
    Get current balance for an account
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get balance
        balance = TransferService.get_account_balance(db, account_number)
        
        return jsonify({
            "account_number": account_number,
            "balance": balance,
            "currency": "USD"
        }), 200
        
    except ValueError as e:
        logger.error(f"Failed to get balance: {e}")
        return jsonify(ErrorResponse(
            error="Failed to get balance",
            details=str(e)
        ).dict()), 404
        
    except Exception as e:
        logger.error(f"Unexpected error getting balance: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to get balance"
        ).dict()), 500

@transfer_bp.route('/validate-transfer', methods=['POST'])
def validate_transfer():
    """
    Validate transfer preconditions without executing the transfer
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
            transfer_data = TransferRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Validation error",
                details=str(e)
            ).dict()), 400
        
        # Get database session
        db = next(get_db())
        
        # Validate transfer preconditions
        validation_result = TransferService.validate_transfer_preconditions(db, transfer_data)
        
        return jsonify({
            "transfer_data": transfer_data.dict(),
            "validation": validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating transfer: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to validate transfer"
        ).dict()), 500

@transfer_bp.route('/account/<account_number>/concurrent-status', methods=['GET'])
def get_concurrent_status(account_number):
    """
    Get information about concurrent operations for an account
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get concurrent status
        status = TransferService.get_concurrent_transfer_status(db, account_number)
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting concurrent status: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to get concurrent status"
        ).dict()), 500

@transfer_bp.route('/transaction-info', methods=['GET'])
def get_transaction_info():
    """
    Get database transaction information and health status
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Get transaction information
        transaction_info = TransactionManager.get_transaction_info(db)
        
        # Get connection health
        connection_health = TransactionManager.check_connection_health(db)
        
        return jsonify({
            "transaction_info": transaction_info,
            "connection_health": connection_health,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transaction info: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="Failed to get transaction info"
        ).dict()), 500

@transfer_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check for transfer service
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Check database connection
        db_healthy = TransactionManager.check_connection_health(db)
        
        # Get transaction info
        transaction_info = TransactionManager.get_transaction_info(db)
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "database_connection": db_healthy,
            "transaction_info": transaction_info,
            "timestamp": datetime.now().isoformat()
        }
        
        status_code = 200 if db_healthy else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503 