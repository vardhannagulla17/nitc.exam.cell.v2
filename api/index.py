from flask import Flask, render_template, request, redirect, session
import os

# Template directory paths
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

# Create Flask app
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'vercel-key-2024'

# Add datetime filter for templates
@app.template_filter('datetime')
def datetime_filter(dt):
    return dt.strftime('%Y-%m-%d %H:%M') if dt else ''

# Template context processor
@app.context_processor
def inject_template_vars():
    from datetime import datetime
    return {
        'total_students': 250,
        'total_courses': 15,
        'total_files': 42,
        'total_semesters': 8,
        'role': 'admin',  # Set as admin to see all features
        # Download page expects semesters as tuples: (id, name, code, type, level)
        'semesters': [
            (1, 'S1', 'CS', 'Regular', 'UG'),
            (2, 'S2', 'CS', 'Regular', 'UG'),
            (3, 'S3', 'CS', 'Regular', 'UG'),
            (4, 'S4', 'CS', 'Regular', 'UG'),
            (5, 'S5', 'CS', 'Regular', 'UG'),
            (6, 'S6', 'CS', 'Regular', 'UG'),
            (7, 'S7', 'CS', 'Regular', 'UG'),
            (8, 'S8', 'CS', 'Regular', 'UG')
        ],
        # Download page expects courses as tuples: (code, title)
        'courses': [
            ('CS101', 'Introduction to Programming'),
            ('CS102', 'Data Structures'),
            ('CS201', 'Algorithms'),
            ('CS202', 'Database Management Systems'),
            ('MATH101', 'Discrete Mathematics'),
            ('MATH102', 'Linear Algebra'),
            ('PHY101', 'Physics I'),
            ('CHE101', 'Chemistry I')
        ],
        # Program levels as simple list
        'program_levels': ['UG', 'PG', 'PhD'],
        'files': [
            {'id': 1, 'filename': 'students_batch_2024.xlsx', 'course': 'Computer Science', 'semester': 1, 'program_level': 'UG'},
            {'id': 2, 'filename': 'course_data.pdf', 'course': 'Mathematics', 'semester': 2, 'program_level': 'UG'}
        ],
        'uploaded_files': [
            {'name': 'students_batch_2024.xlsx', 'size': 2048576, 'uploaded_at': datetime(2024, 12, 19, 10, 30)},
            {'name': 'course_data.pdf', 'size': 870400, 'uploaded_at': datetime(2024, 12, 18, 15, 45)},
            {'name': 'semester_results.xlsx', 'size': 1536000, 'uploaded_at': datetime(2024, 12, 17, 9, 20)}
        ]
    }

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            session['logged_in'] = True
            return redirect('/dashboard')
    
    try:
        return render_template('login.html')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>NITC Login</title>
<style>
body{{font-family:Arial;background:#f8fafc;margin:0;padding:2rem;display:flex;justify-content:center;align-items:center;min-height:100vh}}
.container{{background:white;padding:3rem;border-radius:1rem;box-shadow:0 10px 25px rgba(0,0,0,0.1);max-width:400px;width:100%}}
h1{{color:#2563eb;text-align:center;margin-bottom:2rem}}
.form-group{{margin-bottom:1.5rem}}
input{{width:100%;padding:0.75rem;border:1px solid #ddd;border-radius:0.5rem}}
button{{width:100%;background:#2563eb;color:white;padding:0.75rem;border:none;border-radius:0.5rem;cursor:pointer}}
</style></head>
<body>
<div class="container">
<h1>NITC Exam Cell</h1>
<form method="POST">
<div class="form-group">
<input name="username" type="text" placeholder="Username" required>
</div>
<div class="form-group">
<input name="password" type="password" placeholder="Password" required>
</div>
<button type="submit">Login</button>
</form>
</div>
</body></html>'''

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/login')
    
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>Dashboard</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:1200px;margin:auto}}
.header{{text-align:center;margin-bottom:30px;background:white;padding:20px;border-radius:8px}}
.nav{{background:white;padding:15px;border-radius:8px;margin-bottom:20px}}
.nav a{{margin-right:15px;text-decoration:none;color:#007bff}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:30px}}
.stat-card{{background:white;padding:20px;border-radius:8px;text-align:center}}
.tiles{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.tile{{background:white;padding:30px;border-radius:8px;text-align:center}}
.tile a{{text-decoration:none;color:#333}}
</style></head>
<body>
<div class="container">
<div class="header">
<h1>NITC Exam Cell Dashboard</h1>
</div>
<div class="nav">
<a href="/dashboard">Dashboard</a>
<a href="/upload">Upload</a>
<a href="/download">Download</a>
<a href="/logout">Logout</a>
</div>
<div class="stats">
<div class="stat-card"><h3>250</h3><p>Students</p></div>
<div class="stat-card"><h3>15</h3><p>Courses</p></div>
<div class="stat-card"><h3>42</h3><p>Files</p></div>
</div>
<div class="tiles">
<div class="tile"><a href="/upload"><h3>Upload Files</h3></a></div>
<div class="tile"><a href="/download"><h3>Download Files</h3></a></div>
</div>
</div>
</body></html>'''

@app.route('/upload')
def upload():
    if not session.get('logged_in'):
        return redirect('/login')
    
    try:
        return render_template('upload.html')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>Upload</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto}}
.back-btn{{display:inline-block;margin-bottom:20px;padding:10px 20px;background:#6c757d;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<a href="/dashboard" class="back-btn">Back</a>
<h1>Upload Files</h1>
<p>Upload functionality will use your actual template: {str(e)}</p>
</div>
</body></html>'''

@app.route('/download', methods=['GET', 'POST'])
def download():
    if not session.get('logged_in'):
        return redirect('/login')
    
    # Handle POST requests for form submissions
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action in ['preview', 'download', 'download_all', 'preview_simple', 'download_simple']:
            # Mock response for form actions
            return f'''<!DOCTYPE html>
<html><head><title>Download Action</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:8px}}
.success{{color:#28a745;background:#d4edda;padding:15px;border-radius:5px;margin-bottom:20px}}
.back-btn{{display:inline-block;margin-top:20px;padding:10px 20px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<div class="success">
<h3>✅ Action: {action.replace('_', ' ').title()}</h3>
<p>Form data received successfully!</p>
<p><strong>Program Level:</strong> {request.form.get('program_level', 'Not selected')}</p>
<p><strong>Semester:</strong> {request.form.get('semester_id', 'Not selected')}</p>
<p><strong>Course:</strong> {request.form.get('course_code', 'Not selected')}</p>
<p><strong>Exam Date:</strong> {request.form.get('exam_date', 'Not selected')}</p>
</div>
<p>In a real application, this would generate and download the attendance sheet.</p>
<a href="/download" class="back-btn">← Back to Download Page</a>
</div>
</body></html>'''
    
    # Handle GET requests with optional filtering parameters
    program_level = request.args.get('program_level', '')
    semester_id = request.args.get('semester_id', '')
    
    # Filter semesters and courses based on selected program level
    filtered_semesters = [
        (1, 'S1', 'CS', 'Regular', 'UG'),
        (2, 'S2', 'CS', 'Regular', 'UG'),
        (3, 'S3', 'CS', 'Regular', 'UG'),
        (4, 'S4', 'CS', 'Regular', 'UG'),
        (5, 'S5', 'CS', 'Regular', 'UG'),
        (6, 'S6', 'CS', 'Regular', 'UG'),
        (7, 'S7', 'CS', 'Regular', 'UG'),
        (8, 'S8', 'CS', 'Regular', 'UG')
    ]
    
    filtered_courses = [
        ('CS101', 'Introduction to Programming'),
        ('CS102', 'Data Structures'),
        ('CS201', 'Algorithms'),
        ('CS202', 'Database Management Systems'),
        ('MATH101', 'Discrete Mathematics'),
        ('MATH102', 'Linear Algebra')
    ]
    
    try:
        return render_template('download.html', 
                             semesters=filtered_semesters,
                             courses=filtered_courses,
                             program_levels=['UG', 'PG', 'PhD'],
                             selected_program=program_level,
                             selected_semester=semester_id)
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>Download</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto}}
.back-btn{{display:inline-block;margin-bottom:20px;padding:10px 20px;background:#6c757d;color:white;text-decoration:none;border-radius:5px}}
.error{{background:#f8d7da;color:#721c24;padding:15px;border-radius:5px;margin-bottom:20px}}
</style></head>
<body>
<div class="container">
<a href="/dashboard" class="back-btn">← Back to Dashboard</a>
<h1>Download Files</h1>
<div class="error">Template error: {str(e)}</div>
<p>Attempting to use your sophisticated download template with dynamic form features.</p>
</div>
</body></html>'''

@app.route('/upload_file')
def upload_file():
    # Redirect to the upload page
    return redirect('/upload')

@app.route('/download_attendance')
def download_attendance():
    # Redirect to the download page  
    return redirect('/download')

@app.route('/delete_file/<filename>')
def delete_file(filename):
    # Mock file deletion - in real app this would delete the file
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/favicon.ico')
def favicon():
    return '', 204