from flask import Flask, render_template, request, redirect, session, flash, jsonify
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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in'):
        return redirect('/login')
    
    # Handle POST requests for file uploads
    if request.method == 'POST':
        # Get form data
        academic_year = request.form.get('academic_year', '')
        semester = request.form.get('semester', '')
        program_level = request.form.get('program_level', '')
        uploaded_file = request.files.get('file')
        
        # Mock successful upload response
        return f'''<!DOCTYPE html>
<html><head><title>Upload Success</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:8px}}
.success{{color:#155724;background:#d4edda;padding:20px;border-radius:8px;margin-bottom:20px;border:1px solid #c3e6cb}}
.details{{background:#f8f9fa;padding:15px;border-radius:5px;margin:20px 0}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
h3{{color:#155724;margin-bottom:15px}}
</style></head>
<body>
<div class="container">
<div class="success">
<h3>✅ File Upload Successful!</h3>
<p>Your Excel file has been processed successfully.</p>
</div>
<div class="details">
<h4>Upload Details:</h4>
<p><strong>Academic Year:</strong> {academic_year or 'Not specified'}</p>
<p><strong>Semester:</strong> {semester or 'Not specified'}</p>
<p><strong>Program Level:</strong> {program_level or 'Not specified'}</p>
<p><strong>File:</strong> {uploaded_file.filename if uploaded_file and uploaded_file.filename else 'No file selected'}</p>
<p><strong>File Size:</strong> {f"{len(uploaded_file.read())} bytes" if uploaded_file else "0 bytes"}</p>
</div>
<p><strong>📊 Processing Summary:</strong></p>
<ul>
<li>✅ File validation completed</li>
<li>✅ Data structure verified</li>
<li>✅ Database records updated</li>
<li>✅ Upload logged successfully</li>
</ul>
<p>In a real application, this would process the Excel file and update the database.</p>
<a href="/upload" class="back-btn">← Upload Another File</a>
<a href="/dashboard" class="back-btn" style="background:#28a745;margin-left:10px">📊 Go to Dashboard</a>
</div>
</body></html>'''
    
    # Handle GET requests - show the upload form
    try:
        return render_template('upload.html')
    except Exception as e:
        return f'''<!DOCTYPE html>
<html><head><title>Upload</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:8px}}
.back-btn{{display:inline-block;margin-bottom:20px;padding:10px 20px;background:#6c757d;color:white;text-decoration:none;border-radius:5px}}
.error{{background:#f8d7da;color:#721c24;padding:15px;border-radius:5px;margin-bottom:20px}}
</style></head>
<body>
<div class="container">
<a href="/dashboard" class="back-btn">← Back to Dashboard</a>
<h1>Upload Files</h1>
<div class="error">Template error: {str(e)}</div>
<p>Attempting to use your sophisticated upload template with form handling.</p>
</div>
</body></html>'''

@app.route('/download', methods=['GET', 'POST'])
def download():
    if not session.get('logged_in'):
        return redirect('/login')
    
    # Handle POST requests for form submissions
    if request.method == 'POST':
        action = request.form.get('action', '')
        program_level = request.form.get('program_level', 'Not selected')
        semester_id = request.form.get('semester_id', 'Not selected')
        course_code = request.form.get('course_code', 'Not selected')
        exam_date = request.form.get('exam_date', 'Not selected')
        
        if action in ['preview', 'download', 'download_all', 'preview_simple', 'download_simple']:
            # Simulate different actions with appropriate responses
            if action == 'download_all':
                return f'''<!DOCTYPE html>
<html><head><title>Bulk Download</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:900px;margin:auto;background:white;padding:30px;border-radius:8px}}
.success{{color:#155724;background:#d4edda;padding:20px;border-radius:8px;margin-bottom:20px;border:1px solid #c3e6cb}}
.download-info{{background:#fff3cd;padding:15px;border-radius:5px;margin:15px 0;border:1px solid #ffeaa7}}
.file-list{{background:#f8f9fa;padding:20px;border-radius:8px;margin:20px 0}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
.download-btn{{background:#28a745;margin-left:10px}}
</style></head>
<body>
<div class="container">
<div class="success">
<h3>📦 Bulk Download Generated Successfully!</h3>
<p>All attendance sheets have been prepared for download.</p>
</div>
<div class="download-info">
<h4>📋 Download Details:</h4>
<p><strong>Program Level:</strong> {program_level}</p>
<p><strong>Semester:</strong> {semester_id}</p>
<p><strong>Exam Date:</strong> {exam_date}</p>
<p><strong>Total Courses:</strong> 6 courses</p>
</div>
<div class="file-list">
<h4>📁 Generated Files (ZIP Package):</h4>
<ul>
<li>CS101_Introduction_to_Programming_Attendance.html</li>
<li>CS102_Data_Structures_Attendance.html</li>
<li>CS201_Algorithms_Attendance.html</li>
<li>CS202_Database_Management_Attendance.html</li>
<li>MATH101_Discrete_Mathematics_Attendance.html</li>
<li>MATH102_Linear_Algebra_Attendance.html</li>
</ul>
<p><strong>Package Size:</strong> ~2.4 MB</p>
</div>
<p><strong>📥 In a real application, your download would start automatically.</strong></p>
<a href="/download" class="back-btn">← Back to Download Page</a>
<a href="#" class="back-btn download-btn" onclick="alert('Download would start here!')">📥 Download ZIP File</a>
</div>
</body></html>'''
            
            elif action in ['preview', 'preview_simple']:
                format_type = "Simple" if "simple" in action else "Detailed"
                return f'''<!DOCTYPE html>
<html><head><title>Attendance Sheet Preview</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:1000px;margin:auto;background:white;padding:30px;border-radius:8px}}
.preview-header{{text-align:center;border-bottom:2px solid #333;padding-bottom:20px;margin-bottom:30px}}
.attendance-sheet{{border:1px solid #333;margin:20px 0}}
.sheet-header{{background:#f8f9fa;padding:15px;border-bottom:1px solid #333}}
.student-table{{width:100%;border-collapse:collapse}}
.student-table th,td{{border:1px solid #333;padding:8px;text-align:left}}
.student-table th{{background:#e9ecef;font-weight:bold}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<h2>📋 Attendance Sheet Preview - {format_type} Format</h2>
<div class="preview-header">
<h3>NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</h3>
<h4>EXAMINATION ATTENDANCE SHEET</h4>
<p><strong>Course:</strong> {course_code} | <strong>Date:</strong> {exam_date} | <strong>Semester:</strong> S{semester_id}</p>
</div>
<div class="attendance-sheet">
<div class="sheet-header">
<strong>Course Details:</strong> {course_code} - {"Introduction to Programming" if course_code == "CS101" else "Selected Course"}
</div>
<table class="student-table">
<thead>
<tr>
<th>Roll No</th>
<th>Name</th>
<th>Signature</th>
{"<th>Bio Break</th><th>Additional Sheets</th>" if format_type == "Detailed" else ""}
</tr>
</thead>
<tbody>
<tr><td>CS21B001</td><td>Student Name 1</td><td></td>{"<td></td><td></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B002</td><td>Student Name 2</td><td></td>{"<td></td><td></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B003</td><td>Student Name 3</td><td></td>{"<td></td><td></td>" if format_type == "Detailed" else ""}</tr>
<tr><td colspan="{'5' if format_type == 'Detailed' else '3'}"><em>... (showing 3 of 45 students)</em></td></tr>
</tbody>
</table>
</div>
<p><strong>Invigilator Signature:</strong> _________________________</p>
<a href="/download" class="back-btn">← Back to Download Page</a>
<a href="#" class="back-btn" style="background:#28a745;margin-left:10px" onclick="alert('Download would start here!')">📥 Download This Sheet</a>
</div>
</body></html>'''
            
            else:  # download or download_simple
                format_type = "Simple" if "simple" in action else "Detailed"
                return f'''<!DOCTYPE html>
<html><head><title>Download Complete</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:800px;margin:auto;background:white;padding:30px;border-radius:8px}}
.success{{color:#155724;background:#d4edda;padding:20px;border-radius:8px;margin-bottom:20px;border:1px solid #c3e6cb}}
.download-info{{background:#f8f9fa;padding:15px;border-radius:5px;margin:15px 0}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<div class="success">
<h3>📥 Download Completed Successfully!</h3>
<p>The {format_type.lower()} attendance sheet has been generated.</p>
</div>
<div class="download-info">
<h4>📋 File Details:</h4>
<p><strong>File Name:</strong> {course_code}_Attendance_{format_type}_{exam_date}.html</p>
<p><strong>Course:</strong> {course_code}</p>
<p><strong>Format:</strong> {format_type}</p>
<p><strong>Program Level:</strong> {program_level}</p>
<p><strong>Semester:</strong> {semester_id}</p>
<p><strong>Exam Date:</strong> {exam_date}</p>
<p><strong>File Size:</strong> ~85 KB</p>
</div>
<p><strong>📄 The attendance sheet includes:</strong></p>
<ul>
<li>Student roll numbers and names</li>
<li>Signature columns</li>
{"<li>Bio break tracking</li><li>Additional answer sheets column</li>" if format_type == "Detailed" else ""}
<li>Invigilator signature section</li>
<li>NITC official formatting</li>
</ul>
<p><em>In a real application, the file would be downloaded to your computer.</em></p>
<a href="/download" class="back-btn">← Back to Download Page</a>
<a href="/dashboard" class="back-btn" style="background:#28a745;margin-left:10px">📊 Go to Dashboard</a>
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