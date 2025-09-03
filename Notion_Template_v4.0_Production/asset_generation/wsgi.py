#!/usr/bin/env python3
"""
WSGI configuration for Estate Planning Concierge v4.0 Review Dashboard
Production deployment using Gunicorn or Apache mod_wsgi
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/estate-planning/dashboard.log'),
        logging.StreamHandler()
    ]
)

# Import the Flask application
from review_dashboard import ReviewDashboard

# Create the WSGI application
def create_app():
    """Create and configure the Flask app for WSGI"""
    # Production database path
    db_path = os.getenv('ESTATE_DB_PATH', '/var/lib/estate-planning/estate_planning_assets.db')
    
    # Create dashboard instance  
    dashboard = ReviewDashboard(db_path=db_path, port=5000)
    
    # Configure Flask for production
    dashboard.app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'estate-planning-secret-2024'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file upload
    )
    
    return dashboard.app

# WSGI application
application = create_app()

if __name__ == '__main__':
    # For testing WSGI config locally
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8000, application)
    print("🌐 WSGI server running on http://localhost:8000")
    httpd.serve_forever()