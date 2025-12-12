# Vercel serverless function entry point
import sys
import os

# Get parent directory (project root)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Change to parent directory so relative imports work
os.chdir(parent_dir)

# Add parent directory to Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the Flask app from app.py using importlib to avoid package/module conflict
import importlib.util
spec = importlib.util.spec_from_file_location("main_app", os.path.join(parent_dir, "app.py"))
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)

# Get the Flask app instance - this is what Vercel will use
app = main_app.app