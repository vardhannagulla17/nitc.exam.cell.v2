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
        'semesters': [1, 2, 3, 4, 5, 6, 7, 8],
        'courses': [
            {'id': 1, 'name': 'Computer Science', 'code': 'CS'},
            {'id': 2, 'name': 'Mathematics', 'code': 'MATH'}
        ],
        'program_levels': [
            {'id': 1, 'name': 'Undergraduate', 'code': 'UG'},
            {'id': 2, 'name': 'Postgraduate', 'code': 'PG'}
        ],
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

@app.route('/download')
def download():
    if not session.get('logged_in'):
        return redirect('/login')
    
    try:
        return render_template('download.html')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>Download</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto}}
.back-btn{{display:inline-block;margin-bottom:20px;padding:10px 20px;background:#6c757d;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<a href="/dashboard" class="back-btn">Back</a>
<h1>Download Files</h1>
<p>Download functionality will use your actual template: {str(e)}</p>
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