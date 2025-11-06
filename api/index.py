import os
import sys

# CRITICAL: Set Vercel environment BEFORE any other imports
os.environ['VERCEL'] = '1'
os.environ['FLASK_CONFIG'] = 'vercel'

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now import the app factory from the app package
from app import create_app

# Create the app with Vercel config
app = create_app('vercel')
