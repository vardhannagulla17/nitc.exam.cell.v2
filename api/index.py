from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
import os
import sys
import sqlite3
import pandas as pd
from io import BytesIO
import time

# Set Vercel environment
os.environ['VERCEL'] = '1'

# Create Flask app
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')
app.secret_key = 'vercel-deployment-key-2024'

# Configure for Vercel
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['DOWNLOAD_FOLDER'] = '/tmp/downloads'

# Allowed extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# In-memory storage for Vercel
UPLOAD_STORAGE = {}
DOWNLOAD_STORAGE = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database functions (simplified for Vercel)
def get_db_connection():
    """Get database connection for Vercel"""
    db_path = '/tmp/exam_cell.db'
    return sqlite3.connect(db_path)

def init_db():
    """Initialize database for Vercel"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff'
            )
        ''')
        
        # Create semesters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semesters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year TEXT NOT NULL,
                semester_type TEXT NOT NULL,
                degree_level TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                db_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ('admin', 'pbkdf2:sha256:600000$default$default_hash', 'admin'))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database init error: {e}")
        return False

# Initialize database
init_db()

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication for demo
        if username == 'admin' and password == 'admin':
            session['user_id'] = 1
            session['username'] = 'admin'
            session['role'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Use admin/admin for demo.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html',
                         username=session['username'],
                         role=session['role'],
                         total_students=0,
                         total_courses=0,
                         total_semesters=0,
                         uploaded_files=[])

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Only administrators can upload files.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Store in memory for Vercel
            content = file.read()
            UPLOAD_STORAGE[filename] = {
                'content': content,
                'uploaded_at': time.time()
            }
            flash(f'File {filename} uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type! Please upload Excel files only.', 'error')
    
    return render_template('upload.html')

@app.route('/download', methods=['GET', 'POST'])
def download_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        flash('Download functionality is being configured for Vercel deployment.', 'info')
    
    return render_template('download.html',
                         semesters=[],
                         courses=[],
                         program_levels=['UG', 'PG', 'PhD'],
                         selected_semester=None,
                         selected_program=None)

# Health check for Vercel
@app.route('/health')
def health_check():
    return {'status': 'ok', 'vercel': True, 'app': 'NITC Exam Cell'}

@app.route('/test')
def test_route():
    return '<h1>NITC Exam Cell</h1><p>Vercel deployment test successful!</p><a href="/login">Go to Login</a>'

@app.route('/api/test')
def api_test():
    return {'message': 'API working', 'status': 'success'}

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    try:
        return render_template('error.html', error=error), 404
    except:
        return render_template('error_simple.html'), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template('error.html', error=error), 500
    except:
        return render_template('error_simple.html'), 500

# Catch all exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unhandled exception: {e}")
    try:
        return render_template('error_simple.html'), 500
    except:
        return f"<h1>Error 500</h1><p>Internal Server Error: {str(e)}</p>", 500
