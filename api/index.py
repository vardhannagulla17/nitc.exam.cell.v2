import os
import sys

# Set Vercel environment variable before any imports
os.environ['VERCEL'] = '1'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import using the app factory pattern from app package
# But we need to use app.py not the app/ package, so be explicit
import importlib.util

app_py_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
spec = importlib.util.spec_from_file_location("main_app", app_py_path)
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)

# Export the Flask app for Vercel
app = main_app.app
