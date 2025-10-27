from app import create_app
from app.models import init_db

# Create the Flask application
app = create_app()

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)