"""
Flask Backend API for Planogram Web UI
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / "logs" / "api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'planogram-web-ui-dev-key')
app.config['JSON_SORT_KEYS'] = False  # Preserve key order in JSON responses
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Configure CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure SocketIO
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=True,
    async_mode='eventlet'  # Use eventlet for better performance
)

# Import routes
from api.routes import *

def create_app():
    """Create and configure the Flask application"""
    return app