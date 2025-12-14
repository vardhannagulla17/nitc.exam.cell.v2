from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, current_app, make_response
from werkzeug.utils import secure_filename
import os
import sys
import time
from io import BytesIO
import uuid
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional for production

# Import Supabase client
from supabase_client import supabase

# Add the current directory to Python path so we can import from nitc.exam.cell.v1.app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app and configure it
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nitc-exam-cell-secret-key-2025')

# Supabase bucket name
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'uploads')

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
else:
    # For Vercel, ensure temp directories exist
    for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                print(f'Note: Could not create temp directory {folder}: {str(e)}')

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
        # Try Supabase first if available
        if supabase:
            print("DEBUG: Fetching files from Supabase")
            try:
                result = supabase.storage.from_(SUPABASE_BUCKET).list()
                print(f"DEBUG: Supabase list result: {len(result) if result else 0} files")
                for file_obj in result:
                    if file_obj['name'] and not file_obj['name'].endswith('/'):
                        file_info = {
                            'name': file_obj['name'],
                            'size': file_obj.get('metadata', {}).get('size', 0) or 0,
                            'uploaded_at': datetime.fromisoformat(file_obj['updated_at'].replace('Z', '+00:00')) if file_obj.get('updated_at') else datetime.now()
                        }
                        files.append(file_info)
                        print(f"DEBUG: Added Supabase file: {file_obj['name']}")
            except Exception as e:
                print(f"DEBUG: Error fetching files from Supabase: {str(e)}")
                # Continue to try local filesystem
        
        # Also check local filesystem (or use as fallback)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        else:
            print(f"DEBUG: Checking local filesystem: {UPLOAD_FOLDER}")
            for filename in os.listdir(UPLOAD_FOLDER):
                try:
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.isfile(filepath):
                        # Avoid duplicates if file exists in both places
                        if not any(f['name'] == filename for f in files):
                            file_info = {
                                'name': filename,
                                'size': os.path.getsize(filepath),
                                'uploaded_at': datetime.fromtimestamp(os.path.getctime(filepath))
                            }
                            files.append(file_info)
                            print(f"DEBUG: Added local file: {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
        
        print(f"DEBUG: Total files found: {len(files)}")
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
        from app.database import USE_SUPABASE_DB
        
        if USE_SUPABASE_DB and supabase:
            # Query Supabase for stats
            print("DEBUG: Querying Supabase for semester stats...")
            try:
                semesters_result = supabase.table('semesters').select('id').execute()
                total_semesters = len(semesters_result.data) if semesters_result.data else 0
                print(f"DEBUG: Found {total_semesters} semesters")
                
                students_result = supabase.table('students').select('id, course_code').execute()
                total_students = len(students_result.data) if students_result.data else 0
                print(f"DEBUG: Found {total_students} students")
                
                unique_courses = set(row['course_code'] for row in students_result.data) if students_result.data else set()
                total_courses = len(unique_courses)
                print(f"DEBUG: Found {total_courses} unique courses")
                
                return {
                    'total_students': total_students,
                    'total_courses': total_courses,
                    'total_semesters': total_semesters
                }
            except Exception as e:
                print(f"ERROR querying Supabase in get_semester_stats: {e}")
                return {'total_students': 0, 'total_courses': 0, 'total_semesters': 0}
        else:
            # SQLite for local development
            import sqlite3
            conn = sqlite3.connect('exam_cell.db')
            cursor = conn.cursor()

            # Get all semester databases
            cursor.execute('SELECT db_name FROM semesters')
            semester_dbs = cursor.fetchall()
            
            # Filter out entries whose DB files no longer exist
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
                    
                    # Count total student records
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

def get_database_usage_stats():
    """Get detailed database usage statistics for admin dashboard"""
    try:
        from app.database import USE_SUPABASE_DB
        
        if USE_SUPABASE_DB and supabase:
            # Get breakdown by semester
            semester_breakdown = []
            semesters = supabase.table('semesters').select('id, academic_year, semester_type, degree_level, exam_type').execute()
            
            for sem in semesters.data:
                students = supabase.table('students').select('id').eq('semester_id', sem['id']).execute()
                semester_breakdown.append({
                    'name': f"{sem['academic_year']} {sem['semester_type']} {sem['degree_level']} {sem['exam_type']}",
                    'count': len(students.data) if students.data else 0
                })
            
            # Get total counts
            total_students = supabase.table('students').select('id', count='exact').execute()
            total_semesters = len(semesters.data)
            
            # Estimate database size (rough calculation)
            # Average row size: ~500 bytes (including indexes)
            estimated_db_size_mb = (total_students.count * 500 / 1024 / 1024) if hasattr(total_students, 'count') else 0
            
            return {
                'semester_breakdown': semester_breakdown,
                'total_records': total_students.count if hasattr(total_students, 'count') else 0,
                'total_semesters': total_semesters,
                'estimated_size_mb': round(estimated_db_size_mb, 2),
                'free_tier_limit_mb': 500
            }
        else:
            # SQLite stats
            import os
            db_size = 0
            if os.path.exists('exam_cell.db'):
                db_size = os.path.getsize('exam_cell.db') / 1024 / 1024  # MB
            
            return {
                'semester_breakdown': [],
                'total_records': 0,
                'total_semesters': 0,
                'estimated_size_mb': round(db_size, 2),
                'free_tier_limit_mb': 500
            }
    except Exception as e:
        print(f"Error getting database usage stats: {e}")
        return None

from app.attendance import (
    generate_attendance_sheet,
    generate_all_attendance_sheets_zip
)

# Initialize database for Vercel (serverless) environment
# In local development, this is done in if __name__ == '__main__' block
if IS_VERCEL:
    try:
        init_db()
        print("✅ Database initialized for Vercel environment")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

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

# Test route for Vercel debugging
@app.route('/health')
def health_check():
    """Health check endpoint to verify setup"""
    import os
    from app.database import USE_SUPABASE_DB
    
    is_vercel = bool(os.environ.get('VERCEL'))
    supabase_url = bool(os.environ.get('SUPABASE_URL'))
    supabase_key = bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY'))
    supabase_configured = supabase is not None
    
    status = {
        'status': 'ok',
        'environment': 'Vercel' if is_vercel else 'Local',
        'vercel_detected': is_vercel,
        'supabase_url_set': supabase_url,
        'supabase_key_set': supabase_key,
        'supabase_client_initialized': supabase_configured,
        'using_supabase_db': USE_SUPABASE_DB,
        'python_path': sys.path[:2],
        'base_dir': BASE_DIR
    }
    
    # Add warning if on Vercel without Supabase
    if is_vercel and not USE_SUPABASE_DB:
        status['warning'] = 'Running on Vercel WITHOUT Supabase - data will not persist! Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.'
    
    return status

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
        file_deleted = False
        
        # Try to delete from Supabase first if available
        if supabase:
            print(f"DEBUG: Attempting to delete {filename} from Supabase")
            try:
                result = supabase.storage.from_(SUPABASE_BUCKET).remove([filename])
                print(f"DEBUG: Supabase delete result: {result}")
                if result:
                    file_deleted = True
                    print(f"DEBUG: Successfully deleted from Supabase: {filename}")
            except Exception as e:
                print(f"DEBUG: Error deleting from Supabase: {str(e)}")
        
        # Also try to delete from local filesystem
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                file_deleted = True
                print(f"DEBUG: Successfully deleted from local filesystem: {filename}")
            except Exception as e:
                print(f"DEBUG: Error deleting from filesystem: {str(e)}")
        
        if file_deleted:
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
    
    # Get detailed database usage stats for admin users
    db_usage = None
    if session.get('role') == 'admin':
        db_usage = get_database_usage_stats()
    
    response = make_response(render_template('dashboard.html',
                         username=session['username'],
                         role=session['role'],
                         total_students=stats['total_students'],
                         total_courses=stats['total_courses'],
                         total_semesters=stats['total_semesters'],
                         uploaded_files=uploaded_files,
                         db_usage=db_usage))
    # Prevent caching to ensure real-time stats
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
            
            try:
                # Read file content once
                content = file.read()
                file.seek(0)  # Reset file pointer
                
                # Try Supabase first if available, then fallback to local storage
                supabase_success = False
                if supabase:
                    print(f"DEBUG: Attempting Supabase upload for {filename}")
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    try:
                        result = supabase.storage.from_(SUPABASE_BUCKET).upload(
                            unique_filename, 
                            content,
                            file_options={
                                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                "upsert": "true"
                            }
                        )
                        print(f"DEBUG: Supabase upload result: {result}")
                        if result:
                            supabase_success = True
                            print(f"DEBUG: Successfully uploaded to Supabase: {unique_filename}")
                            # Use BytesIO for processing
                            file_obj = BytesIO(content)
                            success, message = load_excel_to_db(file_obj, academic_year, semester_type, sheet_type, exam_type)
                        else:
                            print("DEBUG: Supabase upload returned empty result")
                    except Exception as supabase_error:
                        print(f"DEBUG: Supabase upload error: {str(supabase_error)}")
                        print(f"DEBUG: Supabase URL configured: {bool(os.environ.get('SUPABASE_URL'))}")
                        print(f"DEBUG: Supabase Key configured: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
                        print(f"DEBUG: Supabase Bucket: {SUPABASE_BUCKET}")
                
                # Fallback to local filesystem if Supabase failed or not available
                if not supabase_success:
                    print(f"DEBUG: Using local filesystem storage for {filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    # Ensure the upload directory exists
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    success, message = load_excel_to_db(filepath, academic_year, semester_type, sheet_type, exam_type)
            except Exception as file_error:
                flash(f'Error saving file: {str(file_error)}', 'error')
                return redirect(request.url)
            
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
                    zip_data, message = generate_all_attendance_sheets_zip(semester_id, exam_date, in_memory=True, program_level=program_level)
                    if zip_data:
                        return send_file(
                            BytesIO(zip_data),
                            mimetype='application/zip',
                            as_attachment=True,
                            download_name=f'attendance_sheets_{semester_id}_{exam_date}.zip'
                        )
                    else:
                        flash(f'Error generating ZIP: {message}', 'error')
                else:
                    # Generate ZIP on filesystem
                    filepath, message = generate_all_attendance_sheets_zip(semester_id, exam_date, program_level=program_level)
                    if filepath and os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True)
                    else:
                        flash(f'Error generating ZIP: {message}', 'error')
                    
            elif action == 'preview' and course_code:
                print(f"DEBUG: Generating preview for {course_code}")
                html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True, program_level=program_level)
                    
                if html_content:
                    return html_content
                else:
                    flash(f'Error generating preview: {message}', 'error')
                    
            elif action == 'download' and course_code:
                print(f"DEBUG: Generating download for {course_code}")
                if IS_VERCEL:
                    # For Vercel, generate in memory and send directly
                    html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True, in_memory=True, program_level=program_level)
                    if html_content:
                        # Create a proper filename for download
                        safe_course = secure_filename(str(course_code))
                        safe_date = secure_filename(str(exam_date))
                        filename = f"Attendance_{safe_course}_{safe_date}.html"
                        return send_file(
                            BytesIO(html_content.encode('utf-8')),
                            mimetype='text/html',
                            as_attachment=True,
                            download_name=filename
                        )
                    else:
                        flash(f'Error generating download: {message}', 'error')
                else:
                    # For local, generate file and send
                    filepath, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=False, program_level=program_level)
                    if filepath and os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True)
                    else:
                        flash(f'Error generating download: {message}', 'error')
            else:
                if not course_code:
                    flash('Please select a course!', 'error')
                else:
                    flash('Invalid action specified!', 'error')
        except Exception as e:
            print(f"DEBUG: Error during attendance sheet generation: {str(e)}")
            flash(f'An error occurred while generating attendance sheet: {str(e)}', 'error')
    
    # Handle program level and semester selection from URL parameters
    program_level = request.args.get('program_level') or selected_program
    semester_id = request.args.get('semester_id') or selected_semester
    
    print(f"Download route: program_level={program_level}, semester_id={semester_id}")
    
    try:
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
    except Exception as e:
        print(f"Error loading semester/course data: {str(e)}")
        flash(f'Error loading data: {str(e)}', 'error')
        courses = []
        semesters = []

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

@app.route('/absentee', methods=['GET', 'POST'])
def absentee_sheet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get all courses from all semesters
    all_courses = []
    try:
        if USE_SUPABASE_DB and supabase:
            # Get all unique courses from Supabase students table
            print(f"DEBUG Absentee: Loading courses from Supabase...")
            result = supabase.table('students').select('course_code, course_title').execute()
            print(f"DEBUG Absentee: Got {len(result.data) if result.data else 0} rows from students table")
            course_set = set()
            for row in result.data:
                course_set.add((row['course_code'], row['course_title']))
            all_courses = sorted(list(course_set), key=lambda x: x[0])
            print(f"DEBUG Absentee: Found {len(all_courses)} unique courses")
        else:
            import sqlite3
            conn = sqlite3.connect('exam_cell.db')
            cursor = conn.cursor()
            cursor.execute('SELECT db_name FROM semesters')
            semester_dbs = cursor.fetchall()
            conn.close()
            
            course_set = set()
            for (db_name,) in semester_dbs:
                if db_name and os.path.exists(db_name):
                    sem_conn = sqlite3.connect(db_name)
                    sem_cursor = sem_conn.cursor()
                    sem_cursor.execute('SELECT DISTINCT course_code, course_title FROM students ORDER BY course_code')
                    courses = sem_cursor.fetchall()
                    for code, title in courses:
                        course_set.add((code, title))
                    sem_conn.close()
            
            all_courses = sorted(list(course_set), key=lambda x: x[0])
    except Exception as e:
        print(f"ERROR loading courses for absentee: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"DEBUG Absentee: Rendering with {len(all_courses)} courses")
    if all_courses:
        print(f"DEBUG Absentee: First few courses: {all_courses[:3]}")
    
    absentees = []
    student_info = None
    course_info = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'search_student':
            course_code = request.form.get('course_code', '').strip()
            roll_no = request.form.get('roll_no', '').strip()
            
            if course_code and roll_no:
                if USE_SUPABASE_DB and supabase:
                    # Search in Supabase students table
                    try:
                        print(f"DEBUG: Searching for course={course_code}, roll={roll_no}")
                        result = supabase.table('students').select('roll_no, name, course_code, course_title').eq('course_code', course_code).eq('roll_no', roll_no).execute()
                        print(f"DEBUG: Search result count: {len(result.data) if result.data else 0}")
                        if result.data and len(result.data) > 0:
                            row = result.data[0]
                            student_info = {
                                'roll_no': row['roll_no'],
                                'name': row['name'],
                                'course_code': row['course_code'],
                                'course_title': row['course_title']
                            }
                            print(f"DEBUG: Found student: {student_info}")
                        else:
                            flash('Student not found for this course and roll number.', 'error')
                    except Exception as e:
                        print(f"ERROR searching student in Supabase: {e}")
                        import traceback
                        traceback.print_exc()
                        flash(f'Error searching for student: {str(e)}', 'error')
                else:
                    import sqlite3
                    conn = sqlite3.connect('exam_cell.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT db_name FROM semesters')
                    semester_dbs = cursor.fetchall()
                    conn.close()
                    
                    for (db_name,) in semester_dbs:
                        if db_name and os.path.exists(db_name):
                            try:
                                sem_conn = sqlite3.connect(db_name)
                                sem_cursor = sem_conn.cursor()
                                sem_cursor.execute(
                                    'SELECT roll_no, name, course_code, course_title FROM students WHERE course_code = ? AND roll_no = ?',
                                    (course_code, roll_no)
                                )
                                result = sem_cursor.fetchone()
                                sem_conn.close()
                                
                                if result:
                                    student_info = {
                                        'roll_no': result[0],
                                        'name': result[1],
                                        'course_code': result[2],
                                        'course_title': result[3]
                                    }
                                    break
                            except:
                                continue
                    
                    if not student_info:
                        flash('Student not found for this course and roll number.', 'error')
            else:
                flash('Please select course and enter roll number.', 'error')
        
        elif action == 'add_absentee':
            roll_no = request.form.get('roll_no', '').strip()
            name = request.form.get('name', '').strip()
            course_code = request.form.get('course_code', '').strip()
            course_title = request.form.get('course_title', '').strip()
            
            if 'absentees' not in session:
                session['absentees'] = []
            
            if not any(a['roll_no'] == roll_no and a['course_code'] == course_code for a in session['absentees']):
                session['absentees'].append({
                    'roll_no': roll_no,
                    'name': name,
                    'course_code': course_code,
                    'course_title': course_title
                })
                session.modified = True
                flash(f'Added {name} ({roll_no}) to absentee list.', 'success')
            else:
                flash('Student already in absentee list.', 'warning')
        
        elif action == 'remove_absentee':
            index = int(request.form.get('index', -1))
            if 'absentees' in session and 0 <= index < len(session['absentees']):
                removed = session['absentees'].pop(index)
                session.modified = True
                flash(f'Removed {removed["name"]} from absentee list.', 'info')
        
        elif action == 'preview_absentees':
            if 'absentees' in session and len(session['absentees']) > 0:
                exam_date = request.form.get('exam_date', datetime.now().strftime('%Y-%m-%d'))
                html_content = generate_absentee_html(session['absentees'], exam_date)
                return html_content
            else:
                flash('No absentees to preview.', 'error')
        
        elif action == 'download_absentees':
            if 'absentees' in session and len(session['absentees']) > 0:
                exam_date = request.form.get('exam_date', datetime.now().strftime('%Y-%m-%d'))
                html_content = generate_absentee_html(session['absentees'], exam_date)
                
                course_code = session['absentees'][0]['course_code']
                filename = f"Absentees_{course_code}_{exam_date}.html"
                
                return send_file(
                    BytesIO(html_content.encode('utf-8')),
                    mimetype='text/html',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                flash('No absentees to download.', 'error')
        
        elif action == 'clear_absentees':
            session.pop('absentees', None)
            session.modified = True
            flash('Absentee list cleared.', 'info')
    
    if 'absentees' in session:
        absentees = session['absentees']
        if len(absentees) > 0:
            course_info = {
                'course_code': absentees[0]['course_code'],
                'course_title': absentees[0]['course_title']
            }
    
    return render_template('absentee.html',
                         all_courses=all_courses,
                         absentees=absentees,
                         course_info=course_info,
                         student_info=student_info)

def generate_absentee_html(absentees, exam_date):
    """Generate HTML for absentee list"""
    if not absentees:
        return ""
    
    # Sort absentees by roll number before generating HTML
    from helpers.utils import sort_by_roll_number
    # Convert dict format to tuple format for sorting
    absentees_tuples = [(a['roll_no'], a['name'], a['course_code'], a['course_title']) for a in absentees]
    sorted_absentees_tuples = sort_by_roll_number(absentees_tuples)
    # Convert back to dict format
    sorted_absentees = [
        {'roll_no': t[0], 'name': t[1], 'course_code': t[2], 'course_title': t[3]}
        for t in sorted_absentees_tuples
    ]
    
    course_code = sorted_absentees[0]['course_code']
    course_title = sorted_absentees[0]['course_title']
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Absentee List - {course_code}</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 15mm;
        }}
        body {{
            font-family: 'Times New Roman', serif;
            margin: 0;
            padding: 20px;
            font-size: 12pt;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 18pt;
            margin: 5px 0;
        }}
        .header h2 {{
            font-size: 14pt;
            margin: 5px 0;
            font-weight: normal;
        }}
        .course-info {{
            margin: 20px 0;
            font-size: 12pt;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 11pt;
        }}
        @media print {{
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>National Institute of Technology Calicut</h1>
        <h2>Absentee List</h2>
    </div>
    
    <div class="course-info">
        <strong>Course Code:</strong> {course_code}<br>
        <strong>Course Title:</strong> {course_title}<br>
        <strong>Exam Date:</strong> {datetime.strptime(exam_date, '%Y-%m-%d').strftime('%d-%m-%Y')}<br>
        <strong>Total Absentees:</strong> {len(sorted_absentees)}
    </div>
    
    <table>
        <thead>
            <tr>
                <th>S.No</th>
                <th>Roll Number</th>
                <th>Student Name</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for idx, student in enumerate(sorted_absentees, 1):
        html += f"""            <tr>
                <td>{idx}</td>
                <td>{student['roll_no']}</td>
                <td>{student['name']}</td>
            </tr>
"""
    
    html += """        </tbody>
    </table>
    
    <div class="footer">
        <p>
            <strong>Invigilator's Signature:</strong> _____________________
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <strong>Date:</strong> _____________________
        </p>
    </div>
</body>
</html>"""
    
    return html

# Initialize the application and run
if __name__ == '__main__':
    # Initialize DB when running locally
    init_db()
    # Use PORT environment variable when provided (platforms like Vercel/containers)
    port = int(os.environ.get('PORT', 5000))
    # For local development, bind only to localhost to show single URL
    # Use 0.0.0.0 only in production/container environments
    if os.environ.get('VERCEL') or os.environ.get('DOCKER'):
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        app.run(debug=True, host='127.0.0.1', port=port)
