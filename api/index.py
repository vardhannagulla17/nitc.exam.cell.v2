# Vercel serverless function entry point
# This imports and exposes the main Flask app from app.py
import sys
import os

# Add parent directory to Python path so all imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import the Flask app - all routes and configurations are in app.py
try:
    from app import app
except Exception as e:
    # Fallback: Create minimal error reporting app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error():
        return f"""
        <h1>Import Error</h1>
        <p>Failed to import main app: {str(e)}</p>
        <p>Python path: {sys.path}</p>
        <p>Current dir: {os.getcwd()}</p>
        <p>Parent dir: {parent_dir}</p>
        <p>Files in parent: {os.listdir(parent_dir) if os.path.exists(parent_dir) else 'N/A'}</p>
        """, 500

# This 'app' variable is what Vercel will use as the WSGI application