# Run the standalone Flask application
# Note: This imports from the standalone app.py, not the app/ package
import sys
import os

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import the app and init_db from the standalone app.py
# We need to import it as a module to avoid name collision with app/ package
import importlib.util
spec = importlib.util.spec_from_file_location("main_app", "app.py")
main_app = importlib.util.module_from_spec(spec)
sys.modules["main_app"] = main_app
spec.loader.exec_module(main_app)

app = main_app.app
init_db = main_app.init_db

if __name__ == '__main__':
    # Initialize the database
    init_db()
    # Run the Flask application
    app.run(debug=True, host='127.0.0.1', port=5000)