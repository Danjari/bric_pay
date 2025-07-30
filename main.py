from flask import Flask
from flask_cors import CORS
import logging

from src.database import init_db
from src.routes.account_routes import account_bp
from src.routes.deposit_routes import deposit_bp
from src.routes.transfer_routes import transfer_bp
from src.routes.validation_routes import validation_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(account_bp)
    app.register_blueprint(deposit_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(validation_bp)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'message': 'BricPay API is running'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("Starting BricPay API server...")
    app.run(debug=True, host='0.0.0.0', port=9000) 