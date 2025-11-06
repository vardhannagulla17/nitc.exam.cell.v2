from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, current_app
from werkzeug.utils import secure_filename
import os
import sys
import time

# Add the current directory to Python path so we can import from nitc.exam.cell.v1.app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app and configure it
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(timestamp):
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# File upload configurations
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IS_VERCEL = os.environ.get('VERCEL') in ('1', 'true', 'True', True)

# Use memory storage for Vercel, filesystem for local dev
if IS_VERCEL:
    from io import BytesIO
    UPLOAD_STORAGE = {}  # In-memory storage for uploads
    DOWNLOAD_STORAGE = {}  # In-memory storage for downloads
    UPLOAD_FOLDER = '/tmp/uploads'  # Vercel allows /tmp for temporary storage
    DOWNLOAD_FOLDER = '/tmp/downloads'
    # Create temp directories in Vercel
    for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
        try:
            os.makedirs(folder, exist_ok=True)
        except:
            pass  # Ignore if can't create in Vercel
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER', os.path.join(BASE_DIR, 'downloads'))
    # Ensure folders exist in local dev
    for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
        if folder:
            os.makedirs(folder, exist_ok=True)

MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Configure app
app.config['BASE_DIR'] = BASE_DIR
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure required directories exist (only for non-Vercel environments)
if not IS_VERCEL:
    for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                print(f'Error creating directory {folder}: {str(e)}')

# Note: Don't create program-level subdirectories at import time. Those
# should be created lazily when needed (see app.attendance). Creating
# many directories during import can fail on read-only or restricted
# deployment environments and causes hard-to-debug crashes.

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_uploaded_files():
    """Get list of uploaded files with their details"""
    files = []
    try:
        if IS_VERCEL:
            # Use in-memory storage on Vercel
            for filename, file_data in UPLOAD_STORAGE.items():
                try:
                    file_info = {
                        'name': filename,
                        'size': len(file_data['content']),
                        'uploaded_at': file_data['uploaded_at']
                    }
                    files.append(file_info)
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
        else:
            # Use filesystem in local development
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                return files

            for filename in os.listdir(UPLOAD_FOLDER):
                try:
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.isfile(filepath):
                        file_info = {
                            'name': filename,
                            'size': os.path.getsize(filepath),
                            'uploaded_at': os.path.getctime(filepath)
                        }
                        files.append(file_info)
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
        
        # Sort files by upload date, newest first
        return sorted(files, key=lambda x: x['uploaded_at'], reverse=True)
    except Exception as e:
        print(f"Error listing uploaded files: {str(e)}")
        return []

# Import other modules
from app.models import (
    init_db, load_excel_to_db, get_user_by_credentials,
    get_all_semesters, get_courses_for_semester,
    get_semesters_for_program_level
)

def get_semester_stats():
    """Calculate actual statistics from the database"""
    try:
        import sqlite3
        conn = sqlite3.connect('exam_cell.db')
        cursor = conn.cursor()

        # Get all semester databases
        cursor.execute('SELECT db_name FROM semesters')
        semester_dbs = cursor.fetchall()
        
        # Filter out entries whose DB files no longer exist and clean them up
        existing_semester_dbs = []
        missing_db_names = []
        for (db_name,) in semester_dbs:
            abs_db_path = db_name if os.path.isabs(db_name) else os.path.join(app.config['BASE_DIR'], db_name)
            if db_name and os.path.exists(abs_db_path):
                existing_semester_dbs.append((db_name,))
            else:
                missing_db_names.append(db_name)
        if missing_db_names:
            try:
                cursor.executemany('DELETE FROM semesters WHERE db_name = ?', [(n,) for n in missing_db_names if n])
                conn.commit()
            except Exception as _cleanup_err:
                pass
        semester_dbs = existing_semester_dbs
        
        total_students = 0
        unique_courses = set()
        total_semesters = len(semester_dbs)

        # Calculate totals from each semester database
        for (db_name,) in semester_dbs:
            try:
                abs_db_path = db_name if os.path.isabs(db_name) else os.path.join(app.config['BASE_DIR'], db_name)
                sem_conn = sqlite3.connect(abs_db_path)
                sem_cursor = sem_conn.cursor()
                
                # Count total student records (each enrollment row)
                sem_cursor.execute('SELECT COUNT(*) FROM students')
                student_count = sem_cursor.fetchone()[0]
                total_students += student_count

                # Get unique course codes
                sem_cursor.execute('SELECT DISTINCT course_code FROM students')
                courses = sem_cursor.fetchall()
                unique_courses.update(course[0] for course in courses)

                sem_conn.close()
            except Exception as e:
                print(f"Error processing semester database {db_name}: {str(e)}")
                continue

        conn.close()
        
        return {
            'total_students': total_students,
            'total_courses': len(unique_courses),
            'total_semesters': total_semesters
        }
    except Exception as e:
        print(f"Error calculating semester stats: {str(e)}")
        return {
            'total_students': 0,
            'total_courses': 0,
            'total_semesters': 0
        }
from app.attendance import (
    generate_attendance_sheet,
    generate_all_attendance_sheets_zip
)

# Error handler for 500 errors
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('error.html', error=error), 500

# Error handler for 404 errors
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=error), 404

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
        
        user = get_user_by_credentials(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/delete_file/<filename>')
def delete_file(filename):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Only administrators can delete files.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f'File {filename} has been deleted successfully.', 'success')
        else:
            flash(f'File {filename} not found.', 'error')
        
        # Also clear semester data and remove semester databases so stats reset to 0
        try:
            import sqlite3
            conn = sqlite3.connect('exam_cell.db')
            cursor = conn.cursor()
            cursor.execute('SELECT db_name FROM semesters')
            semester_dbs = [row[0] for row in cursor.fetchall()]
            cursor.execute('DELETE FROM semesters')
            conn.commit()
            conn.close()
            
            # Remove semester-specific databases
            for db_path in semester_dbs:
                try:
                    if db_path and os.path.exists(db_path):
                        os.remove(db_path)
                except Exception as remove_err:
                    print(f"Warning: could not remove semester db {db_path}: {remove_err}")
        except Exception as cleanup_err:
            print(f"Warning: cleanup after file delete failed: {cleanup_err}")
    except Exception as e:
        flash(f'Error deleting file {filename}: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = get_semester_stats()
    uploaded_files = get_uploaded_files() if session.get('role') == 'admin' else []
    
    return render_template('dashboard.html',
                         username=session['username'],
                         role=session['role'],
                         total_students=stats['total_students'],
                         total_courses=stats['total_courses'],
                         total_semesters=stats['total_semesters'],
                         uploaded_files=uploaded_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Only admin users can access upload functionality
    if session.get('role') != 'admin':
        flash('Access denied. Only administrators can upload files.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        academic_year = request.form.get('academic_year')
        semester_type = request.form.get('semester_type')
        sheet_type = request.form.get('sheet_type')
        exam_type = request.form.get('exam_type')
        
        # Validate form data
        if not all([academic_year, semester_type, sheet_type, exam_type]):
            flash('Please fill in all academic session details!', 'error')
            return redirect(request.url)
        
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            if IS_VERCEL:
                # Store in memory on Vercel
                content = file.read()
                UPLOAD_STORAGE[filename] = {
                    'content': content,
                    'uploaded_at': time.time()
                }
                # Create BytesIO for processing
                file_obj = BytesIO(content)
                success, message = load_excel_to_db(file_obj, academic_year, semester_type, sheet_type, exam_type)
            else:
                # Store on filesystem in local dev
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                success, message = load_excel_to_db(filepath, academic_year, semester_type, sheet_type, exam_type)
            
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type! Please upload Excel files only.', 'error')
    
    return render_template('upload.html')

@app.route('/download', methods=['GET', 'POST'])
def download_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Initialize variables
    courses = []
    selected_semester = None
    selected_program = None
    program_levels = ['UG', 'PG', 'PhD']
    semesters = get_all_semesters()
    
    print("DEBUG: Starting download route")
    print(f"Request method: {request.method}")
    if request.method == 'GET':
        print(f"GET parameters: {request.args}")
    else:
        print(f"POST data: {request.form}")
    
    if request.method == 'POST':
        action = request.form.get('action', 'download')
        program_level = request.form.get('program_level')
        semester_id = request.form.get('semester_id')
        course_code = request.form.get('course_code')
        exam_date = request.form.get('exam_date')
        
        print(f"DEBUG: POST request received with action={action}")
        print(f"program_level={program_level}, semester_id={semester_id}")
        print(f"course_code={course_code}, exam_date={exam_date}")
        
        if not semester_id:
            flash('Please select a semester!', 'error')
            return render_template('download.html', 
                                semesters=semesters, 
                                courses=[],
                                program_levels=program_levels,
                                selected_semester=None,
                                selected_program=program_level)
        
        if not program_level:
            flash('Please select a program level!', 'error')
            return render_template('download.html', 
                                semesters=semesters,
                                courses=[],
                                program_levels=program_levels,
                                selected_semester=semester_id,
                                selected_program=None)
        
        if not exam_date:
            flash('Please select exam date!', 'error')
            return render_template('download.html', 
                                semesters=semesters,
                                courses=get_courses_for_semester(semester_id, program_level),
                                program_levels=program_levels,
                                selected_semester=semester_id,
                                selected_program=program_level)
        
        courses = get_courses_for_semester(semester_id, program_level)
        selected_semester = semester_id
        selected_program = program_level
        
        print(f"DEBUG: Found {len(courses)} courses for semester {semester_id} and program {program_level}")
        
        try:
            if action == 'download_all':
                print("DEBUG: Generating all attendance sheets ZIP")
                if IS_VERCEL:
                    # Generate ZIP in memory
                    zip_data, message = generate_all_attendance_sheets_zip(semester_id, exam_date, in_memory=True)
                    if zip_data:
                        flash(message, 'success')
                        return send_file(
                            BytesIO(zip_data),
                            mimetype='application/zip',
                            as_attachment=True,
                            download_name=f'attendance_sheets_{semester_id}_{exam_date}.zip'
                        )
                else:
                    # Generate ZIP on filesystem
                    filepath, message = generate_all_attendance_sheets_zip(semester_id, exam_date)
                    if filepath:
                        flash(message, 'success')
                        return send_file(filepath, as_attachment=True)
                flash(message, 'error')
                    
            elif action == 'preview' and course_code:
                print(f"DEBUG: Generating preview for {course_code}")
                html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True)
                    
                if html_content:
                    return html_content
                flash(message, 'error')
                    
            elif action == 'download' and course_code:
                print(f"DEBUG: Generating download for {course_code}")
                filepath, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=False)
                    
                if filepath:
                    flash(message, 'success')
                    return send_file(filepath, as_attachment=True)
                flash(message, 'error')
            else:
                if not course_code:
                    flash('Please select a course!', 'error')
                else:
                    flash('Invalid action specified!', 'error')
        except Exception as e:
            print(f"DEBUG: Error during attendance sheet generation: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
    
    # Handle program level and semester selection from URL parameters
    program_level = request.args.get('program_level')
    semester_id = request.args.get('semester_id')
    
    print(f"Download route: program_level={program_level}, semester_id={semester_id}")
    
    if program_level:
        selected_program = program_level
        semesters = get_semesters_for_program_level(program_level)
        print(f"Found {len(semesters)} semesters for program level {program_level}")
    
    if semester_id:
        selected_semester = semester_id
        if program_level:
            print(f"Getting courses for semester {semester_id} and program {program_level}")
            courses = get_courses_for_semester(semester_id, program_level)
        else:
            print(f"Getting all courses for semester {semester_id}")
            courses = get_courses_for_semester(semester_id)
        print(f"Found {len(courses)} courses")

    # Prepare template data
    template_data = {
        'semesters': semesters,
        'courses': courses,
        'program_levels': program_levels,
        'selected_semester': selected_semester,
        'selected_program': selected_program
    }
    
    print("DEBUG: Final template data:")
    print(f"- Semesters: {len(semesters)}")
    print(f"- Courses: {len(courses)}")
    print(f"- Selected semester: {selected_semester}")
    print(f"- Selected program: {selected_program}")
    
    return render_template('download.html', **template_data)

# Initialize the application and run
if __name__ == '__main__':
    # Initialize DB when running locally
    init_db()
    # Use PORT environment variable when provided (platforms like Vercel/containers)
    port = int(os.environ.get('PORT', 5000))
    # Bind to all interfaces in containerized environments (supports both local dev and Docker)
    app.run(debug=True, host='0.0.0.0', port=port)
