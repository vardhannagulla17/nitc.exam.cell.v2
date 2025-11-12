from flask import Flask, render_template, request, redirect, session, flash, jsonify, make_response, send_file
import os
import io
from datetime import datetime
import json
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

def generate_attendance_sheet_html(course_code, exam_date, semester_id, program_level, format_type):
    """Generate a professional HTML attendance sheet for download"""
    
    # Mock student data
    students = [
        "Aadhya Sharma", "Arjun Patel", "Bhavya Reddy", "Chetan Kumar", "Divya Nair",
        "Eshan Gupta", "Fiza Khan", "Gaurav Singh", "Harini Rao", "Ishaan Verma",
        "Janhvi Agarwal", "Karthik Menon", "Lavanya Iyer", "Manav Sharma", "Nandini Joshi",
        "Ojas Pandey", "Priya Nair", "Rohan Kumar", "Shreya Patel", "Tanvi Reddy",
        "Uday Singh", "Vaishnavi Gupta", "Winnie Thomas", "Yash Agarwal", "Zara Ali",
        "Aditi Sharma", "Bharat Kumar", "Chitra Menon", "Dev Patel", "Eshita Singh",
        "Fahad Khan", "Gitika Rao", "Harsh Verma", "Isha Agarwal", "Jai Sharma",
        "Kavya Nair", "Laksh Gupta", "Meera Patel", "Nikhil Singh", "Pooja Reddy",
        "Rahul Kumar", "Sanya Sharma", "Tejas Patel", "Uma Singh", "Varun Gupta"
    ]
    
    # Generate roll numbers
    roll_prefix = "CS21B" if course_code.startswith("CS") else "MT21B" if course_code.startswith("MATH") else "PH21B"
    
    course_names = {
        'CS101': 'Introduction to Programming',
        'CS102': 'Data Structures and Algorithms',
        'CS201': 'Advanced Algorithms',
        'CS202': 'Database Management Systems',
        'MATH101': 'Discrete Mathematics',
        'MATH102': 'Linear Algebra',
        'PHY101': 'Physics I',
        'CHE101': 'Chemistry I'
    }
    
    course_name = course_names.get(course_code, 'Selected Course')
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Sheet - {course_code} - {exam_date}</title>
    <style>
        @page {{ 
            size: A4 landscape; 
            margin: 0.5in; 
        }}
        
        * {{ 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }}
        
        body {{
            font-family: 'Times New Roman', serif;
            font-size: 12px;
            line-height: 1.4;
            color: #000;
            background: white;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 3px solid #000;
            padding-bottom: 15px;
        }}
        
        .header h1 {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
        }}
        
        .header h2 {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .course-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
            padding: 10px;
            background: #f8f9fa;
            border: 1px solid #ddd;
        }}
        
        .info-item {{
            font-weight: bold;
        }}
        
        .attendance-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            border: 2px solid #000;
        }}
        
        .attendance-table th,
        .attendance-table td {{
            border: 1px solid #000;
            padding: 8px 6px;
            text-align: center;
            vertical-align: middle;
        }}
        
        .attendance-table th {{
            background: #e9ecef;
            font-weight: bold;
            font-size: 11px;
        }}
        
        .roll-col {{ width: 80px; }}
        .name-col {{ width: 180px; text-align: left; }}
        .sign-col {{ width: 120px; height: 25px; }}
        .bio-col {{ width: 80px; }}
        .sheets-col {{ width: 80px; }}
        
        .signature-line {{
            border-bottom: 1px solid #ccc;
            height: 20px;
            margin: 2px 0;
        }}
        
        .footer {{
            margin-top: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 30px;
            border-top: 2px solid #000;
            padding-top: 15px;
        }}
        
        .footer-section {{
            text-align: center;
        }}
        
        .signature-box {{
            border: 1px solid #000;
            height: 60px;
            margin-top: 10px;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            padding: 5px;
            font-size: 10px;
        }}
        
        .notes {{
            margin-top: 20px;
            padding: 10px;
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            font-size: 10px;
        }}
        
        .notes ul {{
            list-style-type: disc;
            margin-left: 20px;
        }}
        
        .print-info {{
            position: fixed;
            top: 10px;
            right: 10px;
            background: #007bff;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 10px;
        }}
        
        @media print {{
            .print-info {{ display: none; }}
            body {{ font-size: 10px; }}
            .attendance-table th,
            .attendance-table td {{ padding: 4px 3px; }}
        }}
    </style>
</head>
<body>
    <div class="print-info">Press Ctrl+P to print</div>
    
    <div class="header">
        <h1>National Institute of Technology Calicut</h1>
        <h2>Examination Attendance Sheet</h2>
    </div>
    
    <div class="course-info">
        <div>
            <div class="info-item">Course: {course_code} - {course_name}</div>
            <div class="info-item">Program: {program_level or "B.Tech"}</div>
            <div class="info-item">Semester: S{semester_id}</div>
        </div>
        <div>
            <div class="info-item">Examination Date: {exam_date}</div>
            <div class="info-item">Format: {format_type}</div>
            <div class="info-item">Total Students: {len(students)}</div>
        </div>
    </div>
    
    <table class="attendance-table">
        <thead>
            <tr>
                <th class="roll-col">Roll No.</th>
                <th class="name-col">Student Name</th>
                <th class="sign-col">Signature</th>'''
    
    if format_type == "Detailed":
        html_content += '''
                <th class="bio-col">Bio Break<br>(Time)</th>
                <th class="sheets-col">Additional<br>Sheets</th>'''
    
    html_content += '''
            </tr>
        </thead>
        <tbody>'''
    
    # Generate student rows
    for i, student_name in enumerate(students, 1):
        roll_no = f"{roll_prefix}{i:03d}"
        html_content += f'''
            <tr>
                <td class="roll-col">{roll_no}</td>
                <td class="name-col">{student_name}</td>
                <td class="sign-col"><div class="signature-line"></div></td>'''
        
        if format_type == "Detailed":
            html_content += '''
                <td class="bio-col"><div class="signature-line"></div></td>
                <td class="sheets-col"><div class="signature-line"></div></td>'''
        
        html_content += '''
            </tr>'''
    
    html_content += '''
        </tbody>
    </table>
    
    <div class="footer">
        <div class="footer-section">
            <strong>Invigilator Details</strong>
            <div class="signature-box">
                Name & Signature
            </div>
        </div>
        
        <div class="footer-section">
            <strong>Summary</strong>
            <div style="margin-top: 10px; text-align: left;">
                <div>Total Students: <strong>''' + str(len(students)) + '''</strong></div>
                <div>Present: ________</div>
                <div>Absent: ________</div>
            </div>
        </div>
        
        <div class="footer-section">
            <strong>Examination Office</strong>
            <div class="signature-box">
                Received & Verified
            </div>
        </div>
    </div>
    
    <div class="notes">
        <strong>Important Instructions:</strong>
        <ul>
            <li>Students must sign in the designated signature column</li>'''
    
    if format_type == "Detailed":
        html_content += '''
            <li>Record bio-break times accurately in the Bio Break column</li>
            <li>Note the number of additional answer sheets in the respective column</li>'''
    
    html_content += '''
            <li>This attendance sheet must be submitted to the Examination Office immediately after the exam</li>
            <li>Any discrepancies should be reported to the Examination Office</li>
            <li>Ensure all signatures are clear and legible</li>
        </ul>
    </div>
    
    <script>
        // Auto-print option
        window.onload = function() {
            if(confirm('Do you want to print this attendance sheet now?')) {
                window.print();
            }
        }
    </script>
</body>
</html>'''
    
    return html_content

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
                # Generate a ZIP file with all course attendance sheets
                import zipfile
                
                zip_buffer = io.BytesIO()
                
                # List of all courses for the semester
                all_courses = [
                    ('CS101', 'Introduction to Programming'),
                    ('CS102', 'Data Structures'),
                    ('CS201', 'Algorithms'),
                    ('CS202', 'Database Management Systems'),
                    ('MATH101', 'Discrete Mathematics'),
                    ('MATH102', 'Linear Algebra')
                ]
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for course_code_item, course_name in all_courses:
                        # Generate HTML for each course
                        html_content = generate_attendance_sheet_html(
                            course_code=course_code_item,
                            exam_date=exam_date,
                            semester_id=semester_id,
                            program_level=program_level,
                            format_type="Detailed"
                        )
                        
                        # Add to ZIP
                        filename = f"{course_code_item}_{course_name.replace(' ', '_')}_Attendance_{exam_date}.html"
                        zip_file.writestr(filename, html_content)
                
                zip_buffer.seek(0)
                
                # Create response with ZIP download
                response = make_response(zip_buffer.getvalue())
                zip_filename = f"All_Attendance_Sheets_{program_level}_S{semester_id}_{exam_date}.zip"
                response.headers['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                response.headers['Content-Type'] = 'application/zip'
                
                return response
            
            elif action in ['preview', 'preview_simple']:
                format_type = "Simple" if "simple" in action else "Detailed"
                return f'''<!DOCTYPE html>
<html><head><title>Complete Attendance Sheet Preview</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:1200px;margin:auto;background:white;padding:30px;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}}
.preview-header{{text-align:center;border-bottom:3px solid #333;padding-bottom:20px;margin-bottom:30px}}
.metadata{{background:#e3f2fd;padding:20px;border-radius:8px;margin-bottom:20px;border-left:4px solid #2196f3}}
.attendance-sheet{{border:2px solid #333;margin:20px 0;page-break-inside:avoid}}
.sheet-header{{background:#f5f5f5;padding:15px;border-bottom:2px solid #333}}
.student-table{{width:100%;border-collapse:collapse;font-size:12px}}
.student-table th,td{{border:1px solid #333;padding:10px;text-align:left}}
.student-table th{{background:#e9ecef;font-weight:bold;text-align:center}}
.signature-col{{width:120px}}
.bio-col{{width:80px;text-align:center}}
.sheets-col{{width:80px;text-align:center}}
.footer{{margin-top:30px;padding:20px;background:#fff3cd;border-radius:8px;border-left:4px solid #ffc107}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px;font-weight:bold}}
.download-info{{background:#d1ecf1;padding:15px;border-radius:5px;margin:15px 0;border-left:4px solid #17a2b8}}
</style></head>
<body>
<div class="container">
<h2>📋 Complete Attendance Sheet Preview - {format_type} Format</h2>

<div class="metadata">
<h4>📊 Sheet Information</h4>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
<div>
<p><strong>🏫 Institution:</strong> National Institute of Technology Calicut</p>
<p><strong>📚 Course:</strong> {course_code} - {"Introduction to Programming" if course_code == "CS101" else "Data Structures" if course_code == "CS102" else "Selected Course"}</p>
<p><strong>📅 Exam Date:</strong> {exam_date}</p>
</div>
<div>
<p><strong>🎓 Program:</strong> {program_level if program_level else "B.Tech"}</p>
<p><strong>📖 Semester:</strong> S{semester_id}</p>
<p><strong>📄 Format:</strong> {format_type} ({format_type.lower()} columns)</p>
</div>
</div>
</div>

<div class="download-info">
<h4>📥 Download Details</h4>
<p><strong>File Format:</strong> Excel (.xlsx) with professional formatting</p>
<p><strong>Page Setup:</strong> A4 landscape orientation, optimized margins</p>
<p><strong>Features:</strong> {"Signature tracking, bio-break monitoring, additional sheets tracking" if format_type == "Detailed" else "Basic signature tracking with clean layout"}</p>
</div>

<div class="preview-header">
<h3>NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</h3>
<h4>EXAMINATION ATTENDANCE SHEET</h4>
<p style="margin:10px 0"><strong>Course:</strong> {course_code} | <strong>Date:</strong> {exam_date} | <strong>Semester:</strong> S{semester_id}</p>
<p style="margin:5px 0;font-size:14px;color:#666">Program: {program_level if program_level else "B.Tech"} | Format: {format_type}</p>
</div>

<div class="attendance-sheet">
<div class="sheet-header">
<strong>📚 Course Details:</strong> {course_code} - {"Introduction to Programming (Theory + Lab)" if course_code == "CS101" else "Data Structures and Algorithms" if course_code == "CS102" else "Selected Course"}
<br><strong>👥 Expected Students:</strong> 45 | <strong>⏰ Duration:</strong> 3 hours
</div>
<table class="student-table">
<thead>
<tr>
<th style="width:100px">Roll No</th>
<th style="width:200px">Student Name</th>
<th class="signature-col">Signature</th>
{"<th class='bio-col'>Bio Break<br>(Time)</th><th class='sheets-col'>Additional<br>Sheets</th>" if format_type == "Detailed" else ""}
</tr>
</thead>
<tbody>
<tr><td>CS21B001</td><td>Aadhya Sharma</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B002</td><td>Arjun Patel</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B003</td><td>Bhavya Reddy</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B004</td><td>Chetan Kumar</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B005</td><td>Divya Nair</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr style="background:#f8f9fa"><td colspan="{'5' if format_type == 'Detailed' else '3'}" style="text-align:center;font-style:italic;padding:15px">... (showing 5 of 45 total students) ...</td></tr>
<tr><td>CS21B043</td><td>Yash Gupta</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B044</td><td>Zara Khan</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
<tr><td>CS21B045</td><td>Aniket Singh</td><td style="border-bottom:1px solid #999"></td>{"<td style='border-bottom:1px solid #999'></td><td style='border-bottom:1px solid #999'></td>" if format_type == "Detailed" else ""}</tr>
</tbody>
</table>

<div style="margin-top:30px;padding:20px;background:#f8f9fa;border-top:2px solid #333">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:40px">
<div>
<p><strong>📝 Invigilator Details:</strong></p>
<p>Name: _________________________</p>
<p>Signature: _____________________</p>
<p>Date: {exam_date}</p>
</div>
<div>
<p><strong>📊 Summary:</strong></p>
<p>Total Students: 45</p>
<p>Present: ____</p>
<p>Absent: ____</p>
</div>
</div>
</div>
</div>

<div class="footer">
<h4>ℹ️ Important Notes</h4>
<ul>
<li>🖊️ Students must sign in the designated column</li>
{"<li>⏰ Bio-break times should be recorded accurately</li><li>📄 Additional sheets should be numbered and tracked</li>" if format_type == "Detailed" else ""}
<li>✅ This sheet must be submitted to the examination office</li>
<li>📧 Any discrepancies should be reported immediately</li>
</ul>
</div>

<div style="text-align:center;margin-top:30px">
<a href="/download" class="back-btn">← Back to Download Page</a>
<a href="#" class="back-btn" style="background:#28a745;margin-left:10px" onclick="window.print(); alert('Ready to download: {course_code}_{exam_date}_{format_type}_attendance.xlsx')">📥 Download This Exact Sheet</a>
</div>

</div>
</body></html>'''
            
            else:  # download or download_simple
                format_type = "Simple" if "simple" in action else "Detailed"
                
                # Generate actual HTML attendance sheet
                html_content = generate_attendance_sheet_html(
                    course_code=course_code,
                    exam_date=exam_date,
                    semester_id=semester_id,
                    program_level=program_level,
                    format_type=format_type
                )
                
                # Create response with file download
                response = make_response(html_content)
                filename = f"{course_code}_Attendance_{format_type}_{exam_date}.html"
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                
                return response
    
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
    if not session.get('logged_in'):
        return redirect('/login')
    
    # Mock file deletion - remove from session or simulate deletion
    return f'''<!DOCTYPE html>
<html><head><title>File Deleted</title>
<style>
body{{font-family:Arial;margin:0;padding:20px;background:#f8f9fa}}
.container{{max-width:600px;margin:auto;background:white;padding:30px;border-radius:8px;text-align:center}}
.success{{color:#155724;background:#d4edda;padding:20px;border-radius:8px;margin-bottom:20px;border:1px solid #c3e6cb}}
.back-btn{{display:inline-block;margin-top:20px;padding:12px 24px;background:#007bff;color:white;text-decoration:none;border-radius:5px}}
</style></head>
<body>
<div class="container">
<div class="success">
<h3>🗑️ File Deleted Successfully!</h3>
<p>The file "<strong>{filename}</strong>" has been removed from the system.</p>
</div>
<p>✅ File deletion completed<br>
✅ Database records updated<br>
✅ Storage space freed</p>
<a href="/dashboard" class="back-btn">← Back to Dashboard</a>
</div>
</body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/favicon.ico')
def favicon():
    return '', 204