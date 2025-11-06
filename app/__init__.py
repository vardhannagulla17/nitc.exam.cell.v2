from flask import Flask
import os

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        # Use vercel config if running on Vercel
        if os.environ.get('VERCEL'):
            config_name = 'vercel'
        else:
            config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    from config import config
    app.config.from_object(config[config_name])
    
    # Ensure required directories exist
    from helpers.file_utils import ensure_directories_exist
    with app.app_context():
        ensure_directories_exist()
    
    # Add datetime filter
    @app.template_filter('datetime')
    def format_datetime(timestamp):
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Register blueprints or import routes
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app