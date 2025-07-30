from flask import Flask, jsonify
from flask_cors import CORS
import logging
from config import settings
from src.database import init_db
from src.routes.account_routes import account_bp

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.secret_key

# Add CORS support
CORS(app, origins=settings.allowed_hosts)

# Initialize database
init_db()

# Register blueprints
app.register_blueprint(account_bp)

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Welcome to Bric Pay API",
        "version": settings.version,
        "status": "running"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version
    })

@app.route('/api/v1/health')
def api_health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "api_version": "v1",
        "service": settings.project_name
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=settings.debug
    ) 