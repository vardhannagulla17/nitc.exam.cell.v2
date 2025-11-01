import os
import sys

# Set Vercel environment variable
os.environ['VERCEL'] = '1'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We need to import from the app.py module, not the app package
# Python will try to import from the app/ directory first, so we need to be explicit
import importlib.util
spec = importlib.util.spec_from_file_location("application", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"))
application_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(application_module)

# Export the app
app = application_module.app
