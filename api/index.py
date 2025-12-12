# Import the main Flask app from app.py
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the actual Flask app
from app import app

# This is the WSGI application Vercel will use
# No need to redefine routes - they're already in app.py