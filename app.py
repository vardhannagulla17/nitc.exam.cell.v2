from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, current_app, make_response, jsonify
from werkzeug.utils import secure_filename
import os
import sys
import time
from io import BytesIO
import uuid
from datetime import datetime
from xhtml2pdf import pisa

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional for production

# Import Supabase client
from supabase_client import supabase

# Import absentee storage for bucket operations
from helpers.supabase_storage import absentee_storage

# Import database utilities
from app.database import USE_SUPABASE_DB

# Add the current directory to Python path so we can import from nitc.exam.cell.v1.app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create Flask app and configure it
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'nitc-exam-cell-secret-key-2025')

# Configure permanent session (for "Remember Me" feature)
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Supabase bucket name
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'uploads')

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(timestamp):
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

# Helper function to convert HTML to PDF
def html_to_pdf(source_html):
    """Convert HTML string to PDF bytes"""
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(source_html.encode("utf-8")), result)
    if pdf.err:
        return None
    return result.getvalue()

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
    init_db, load_excel_to_db, get_user_by_credentials, register_user,
    get_all_semesters, get_courses_for_semester,
    get_semesters_for_program_level,
    get_all_users, get_pending_users, get_pending_users_count, approve_user, reject_user,
    toggle_user_active, update_user_role, delete_user,
    upload_exam_timetable, get_exam_date_for_course, get_timetable_for_semester,
    get_courses_with_exam_dates, has_timetable_for_semester,
    create_password_reset_request, verify_password_reset_otp
)

# Simple in-memory cache for dashboard stats
_stats_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 604800  # Cache for 7 days (effectively infinite - only invalidated on data changes)
}

# Cache for database usage stats (admin only)
_db_usage_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 604800  # Cache for 7 days (effectively infinite - only invalidated on data changes)
}

def invalidate_stats_cache():
    """Invalidate the stats cache to force refresh on next request"""
    global _stats_cache, _db_usage_cache
    _stats_cache['data'] = None
    _stats_cache['timestamp'] = 0
    _db_usage_cache['data'] = None
    _db_usage_cache['timestamp'] = 0
    print("Stats cache and DB usage cache invalidated")

def get_semester_stats(force_refresh=False):
    """Calculate actual statistics from the database with caching
    
    Args:
        force_refresh: If True, bypass cache and recalculate stats
    """
    global _stats_cache
    
    # Check if we have valid cached data
    current_time = time.time()
    cache_age = current_time - _stats_cache['timestamp']
    
    if not force_refresh and _stats_cache['data'] is not None and cache_age < _stats_cache['ttl']:
        print(f"Using cached stats (age: {cache_age:.1f}s)")
        return _stats_cache['data']
    
    # Cache miss or expired - recalculate
    print("Recalculating stats (cache miss or expired)")
    try:
        from app.database import USE_SUPABASE_DB
        
        if USE_SUPABASE_DB and supabase:
            # Query Supabase for stats
            print("DEBUG: Querying Supabase for semester stats...")
            try:
                semesters_result = supabase.table('semesters').select('id').execute()
                total_semesters = len(semesters_result.data) if semesters_result.data else 0
                print(f"DEBUG: Found {total_semesters} semesters")
                
                # Handle pagination for students - fetch all records
                all_students = []
                page_size = 1000
                offset = 0
                
                while True:
                    students_result = supabase.table('students').select('id, course_code').range(offset, offset + page_size - 1).execute()
                    if not students_result.data:
                        break
                    all_students.extend(students_result.data)
                    if len(students_result.data) < page_size:
                        break
                    offset += page_size
                
                total_students = len(all_students)
                print(f"DEBUG: Found {total_students} students (paginated)")
                
                unique_courses = set(row['course_code'] for row in all_students)
                total_courses = len(unique_courses)
                print(f"DEBUG: Found {total_courses} unique courses")
                
                stats = {
                    'total_students': total_students,
                    'total_courses': total_courses,
                    'total_semesters': total_semesters
                }
                
                # Update cache for Supabase stats
                _stats_cache['data'] = stats
                _stats_cache['timestamp'] = time.time()
                print(f"Stats cached: {stats}")
                
                return stats
            except Exception as e:
                print(f"ERROR querying Supabase in get_semester_stats: {e}")
                # Don't cache errors
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
            
            stats = {
                'total_students': total_students,
                'total_courses': len(unique_courses),
                'total_semesters': total_semesters
            }
            
            # Update cache
            _stats_cache['data'] = stats
            _stats_cache['timestamp'] = time.time()
            print(f"Stats cached: {stats}")
            
            return stats
    except Exception as e:
        print(f"Error calculating semester stats: {str(e)}")
        # Don't cache errors
        return {
            'total_students': 0,
            'total_courses': 0,
            'total_semesters': 0
        }

def get_database_usage_stats():
    """Get detailed database usage statistics for admin dashboard with caching"""
    global _db_usage_cache
    
    # Check if we have valid cached data
    current_time = time.time()
    cache_age = current_time - _db_usage_cache['timestamp']
    
    if _db_usage_cache['data'] is not None and cache_age < _db_usage_cache['ttl']:
        print(f"Using cached DB usage stats (age: {cache_age:.1f}s)")
        return _db_usage_cache['data']
    
    # Cache miss or expired - recalculate
    print("Recalculating DB usage stats (cache miss or expired)")
    
    try:
        from app.database import USE_SUPABASE_DB
        
        if USE_SUPABASE_DB and supabase:
            # Get breakdown by semester
            semester_breakdown = []
            semesters = supabase.table('semesters').select('id, academic_year, semester_type, degree_level, exam_type').execute()
            
            for sem in semesters.data:
                # Handle pagination for student count per semester
                student_count = 0
                page_size = 1000
                offset = 0
                
                while True:
                    students = supabase.table('students').select('id').eq('semester_id', sem['id']).range(offset, offset + page_size - 1).execute()
                    if not students.data:
                        break
                    student_count += len(students.data)
                    if len(students.data) < page_size:
                        break
                    offset += page_size
                
                semester_breakdown.append({
                    'name': f"{sem['academic_year']} {sem['semester_type']} {sem['degree_level']} {sem['exam_type']}",
                    'count': student_count
                })
            
            # Get total counts
            total_students = supabase.table('students').select('id', count='exact').execute()
            total_semesters = len(semesters.data)
            
            # Estimate database size (rough calculation)
            # Average row size: ~500 bytes (including indexes)
            estimated_db_size_mb = (total_students.count * 500 / 1024 / 1024) if hasattr(total_students, 'count') else 0
            
            result = {
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
            
            result = {
                'semester_breakdown': [],
                'total_records': 0,
                'total_semesters': 0,
                'estimated_size_mb': round(db_size, 2),
                'free_tier_limit_mb': 500
            }
        
        # Cache the result
        _db_usage_cache['data'] = result
        _db_usage_cache['timestamp'] = time.time()
        print(f"DB usage stats cached at {_db_usage_cache['timestamp']}")
        
        return result
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
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Please enter both email and password!', 'error')
            return render_template('login.html')
        
        try:
            print(f"DEBUG: Attempting login for user: {email}")
            print(f"DEBUG: Supabase client available: {supabase is not None}")
            print(f"DEBUG: USE_SUPABASE_DB: {USE_SUPABASE_DB}")
            
            user = get_user_by_credentials(email, password)
            print(f"DEBUG: get_user_by_credentials returned: {user}")
            
            if user:
                # Check for error responses (pending approval, disabled)
                if isinstance(user, dict) and 'error' in user:
                    if user['error'] == 'pending_approval':
                        flash('Your account is pending admin approval. Please wait.', 'warning')
                    elif user['error'] == 'account_disabled':
                        flash('Your account has been disabled. Contact admin.', 'error')
                    return render_template('login.html')
                
                # Set session permanent if remember me is checked
                if remember:
                    session.permanent = True
                    print(f"DEBUG: Session set to permanent (7 days) for {email}")
                else:
                    session.permanent = False
                    print(f"DEBUG: Session set to temporary (browser session) for {email}")
                
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['username'] = user['email']  # For backward compatibility with marked_by field
                session['full_name'] = user['full_name']
                session['role'] = user['role']
                flash(f'Welcome back, {user["full_name"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'error')
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Login error: {e}")
            print(f"Full traceback: {error_details}")
            flash(f'An error occurred during login: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([email, full_name, password, confirm_password]):
            flash('All fields are required!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
        
        # Validate NITC email domain
        if not email.endswith('@nitc.ac.in'):
            flash('Only @nitc.ac.in email addresses are allowed!', 'error')
            return render_template('register.html')
        
        # Import OTP functions
        from app.models import create_pending_registration
        
        # Create pending registration and send OTP
        success, message, _ = create_pending_registration(email, full_name, password)
        if success:
            flash(message, 'success')
            # Store email in session for OTP verification page
            session['pending_email'] = email
            return redirect(url_for('verify_otp'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Handle OTP verification for email-based registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    # Check if there's a pending email
    pending_email = session.get('pending_email')
    if not pending_email:
        flash('No pending registration found. Please register first.', 'error')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        
        if not otp:
            flash('Please enter the OTP!', 'error')
            return render_template('verify_otp.html', email=pending_email)
        
        # Import verification function
        from app.models import verify_otp_and_register
        
        # Verify OTP and complete registration
        success, message = verify_otp_and_register(pending_email, otp)
        if success:
            # Clear pending email from session
            session.pop('pending_email', None)
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('verify_otp.html', email=pending_email)


@app.route('/resend-otp', methods=['POST'])
def resend_otp_route():
    """Resend OTP to pending registration email"""
    pending_email = session.get('pending_email')
    if not pending_email:
        flash('No pending registration found. Please register first.', 'error')
        return redirect(url_for('register'))
    
    from app.models import resend_otp
    
    success, message = resend_otp(pending_email)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('verify_otp'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address!', 'error')
            return render_template('forgot_password.html')
        
        success, message = create_password_reset_request(email)
        flash(message, 'success' if success else 'error')
        
        if success:
            session['reset_email'] = email
            return redirect(url_for('reset_password'))
        
        return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    reset_email = session.get('reset_email')
    if not reset_email:
        flash('Please request a password reset first.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not otp or not new_password or not confirm_password:
            flash('Please fill in all fields!', 'error')
            return render_template('reset_password.html', email=reset_email)
        
        if new_password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('reset_password.html', email=reset_email)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('reset_password.html', email=reset_email)
        
        success, message = verify_password_reset_otp(reset_email, otp, new_password)
        flash(message, 'success' if success else 'error')
        
        if success:
            session.pop('reset_email', None)
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', email=reset_email)
    
    return render_template('reset_password.html', email=reset_email)

# Admin User Management Routes
@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    all_users = get_all_users()
    pending_users = get_pending_users()
    
    return render_template('admin_users.html', 
                         users=all_users, 
                         pending_users=pending_users)

@app.route('/admin/users/approve/<int:user_id>', methods=['POST'])
def approve_user_route(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    success, message = approve_user(user_id, session.get('email'))
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/reject/<int:user_id>', methods=['POST'])
def reject_user_route(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    success, message = reject_user(user_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
def toggle_user_route(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    success, message = toggle_user_active(user_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/role/<int:user_id>', methods=['POST'])
def change_role_route(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    new_role = request.form.get('role', 'staff')
    success, message = update_user_role(user_id, new_role)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user_route(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('dashboard'))
    
    success, message = delete_user(user_id, session.get('user_id'))
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_users'))

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
            
            # Invalidate stats cache after cleanup
            invalidate_stats_cache()
        except Exception as cleanup_err:
            print(f"Warning: cleanup after file delete failed: {cleanup_err}")
    except Exception as e:
        flash(f'Error deleting file {filename}: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        stats = get_semester_stats()
    except Exception as e:
        print(f"Error getting semester stats: {e}")
        stats = {'total_students': 0, 'total_courses': 0, 'total_semesters': 0}
    
    # Optimize: Only load uploaded files for admin users who need them
    try:
        uploaded_files = get_uploaded_files() if session.get('role') == 'admin' else []
    except Exception as e:
        print(f"Error getting uploaded files: {e}")
        uploaded_files = []
    
    # Get detailed database usage stats for admin users
    db_usage = None
    pending_users_count = 0
    if session.get('role') == 'admin':
        try:
            db_usage = get_database_usage_stats()
        except Exception as e:
            print(f"Error getting database usage stats: {e}")
            db_usage = None
        try:
            # Optimize: Use count query instead of loading all pending users
            pending_users_count = get_pending_users_count()
        except Exception as e:
            print(f"Error getting pending users: {e}")
            pending_users_count = 0
    
    response = make_response(render_template('dashboard.html',
                         username=session.get('full_name', session.get('email', 'User')),
                         role=session['role'],
                         total_students=stats['total_students'],
                         total_courses=stats['total_courses'],
                         total_semesters=stats['total_semesters'],
                         uploaded_files=uploaded_files,
                         db_usage=db_usage,
                         pending_users_count=pending_users_count))
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
                # Invalidate stats cache after successful upload
                invalidate_stats_cache()
                flash(message, 'success')
            else:
                flash(message, 'error')
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type! Please upload Excel files only.', 'error')
    
    return render_template('upload.html')

# ============================================
# EXAM TIMETABLE MANAGEMENT
# ============================================

@app.route('/timetable', methods=['GET', 'POST'])
def manage_timetable():
    """Manage exam timetable - upload and view"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Only admin can upload timetable
    if session.get('role') != 'admin':
        flash('Access denied. Only administrators can manage timetables.', 'error')
        return redirect(url_for('dashboard'))
    
    semesters = get_all_semesters()
    selected_semester = request.args.get('semester_id')
    timetable = []
    
    if request.method == 'POST':
        semester_id = request.form.get('semester_id')
        
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and (allowed_file(file.filename) or file.filename.lower().endswith('.pdf')):
            try:
                # Detect file type
                filename_lower = file.filename.lower()
                if filename_lower.endswith('.pdf'):
                    file_type = 'pdf'
                else:
                    file_type = 'excel'
                
                # Read file content
                content = BytesIO(file.read())
                
                success, message = upload_exam_timetable(
                    content, 
                    semester_id, 
                    session.get('email', 'admin'),
                    file_type=file_type
                )
                
                if success:
                    flash(message, 'success')
                else:
                    flash(message, 'error')
                
                return redirect(url_for('manage_timetable', semester_id=semester_id))
            except Exception as e:
                flash(f'Error uploading timetable: {str(e)}', 'error')
        else:
            flash('Invalid file type! Please upload Excel or PDF files.', 'error')
    
    # Get timetable for selected semester
    if selected_semester:
        timetable = get_timetable_for_semester(selected_semester)
    
    return render_template('timetable.html', 
                         semesters=semesters, 
                         timetable=timetable,
                         selected_semester=selected_semester)

@app.route('/api/exam-date/<semester_id>/<course_code>', methods=['GET'])
def api_get_exam_date(semester_id, course_code):
    """Get exam date for a course via AJAX"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        exam_info = get_exam_date_for_course(course_code, semester_id)
        if exam_info:
            return jsonify({
                'success': True,
                'exam_date': exam_info.get('exam_date'),
                'exam_time': exam_info.get('exam_time'),
                'venue': exam_info.get('venue')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No exam scheduled for this course'
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses-with-dates/<semester_id>/<program_level>', methods=['GET'])
def api_get_courses_with_dates(semester_id, program_level):
    """Get courses with exam dates for a semester and program level"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        courses = get_courses_with_exam_dates(semester_id, program_level)
        return jsonify({'success': True, 'courses': courses}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoints for AJAX requests (no page reload)
@app.route('/api/semesters/<program_level>', methods=['GET'])
def api_get_semesters(program_level):
    """Get semesters for a program level via JSON API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        semesters = get_semesters_for_program_level(program_level)
        # Convert to JSON-friendly format
        # Format: "2025-26 Monsoon (COMBINED, Midsem)"
        result = [{'id': sem[0], 'name': f"{sem[1]} {sem[2].capitalize()} ({sem[3].upper()}, {sem[4].capitalize()})"} for sem in semesters]
        return jsonify({'semesters': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<semester_id>/<program_level>', methods=['GET'])
def api_get_courses(semester_id, program_level):
    """Get courses for a semester and program level via JSON API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        courses = get_courses_for_semester(semester_id, program_level)
        # Convert to JSON-friendly format
        result = [{'code': course[0], 'title': course[1]} for course in courses]
        return jsonify({'courses': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sections/<semester_id>/<course_code>', methods=['GET'])
def api_get_sections(semester_id, course_code):
    """Get sections/batches for a specific course via JSON API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if USE_SUPABASE_DB and supabase:
            # Get unique sections with their instructors
            all_records = []
            page_size = 1000
            offset = 0
            
            while True:
                result = supabase.table('students')\
                    .select('timetable_batch, main_instructor')\
                    .eq('semester_id', semester_id)\
                    .eq('course_code', course_code)\
                    .range(offset, offset + page_size - 1)\
                    .execute()
                if not result.data:
                    break
                all_records.extend(result.data)
                if len(result.data) < page_size:
                    break
                offset += page_size
            
            # Get unique sections with their instructors
            sections_dict = {}
            for record in all_records:
                batch = record.get('timetable_batch')
                instructor = record.get('main_instructor', 'Unknown')
                if batch and batch not in sections_dict:
                    sections_dict[batch] = instructor
            
            # Convert to list and sort
            sections = [{'code': code, 'instructor': instructor} for code, instructor in sorted(sections_dict.items())]
            
            return jsonify({'sections': sections}), 200
        else:
            return jsonify({'sections': []}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instructors/<course_code>', methods=['GET'])
def api_get_instructors(course_code):
    """Get unique instructors for a specific course via JSON API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        if USE_SUPABASE_DB and supabase:
            # Get unique instructors for the course
            all_records = []
            page_size = 1000
            offset = 0
            
            while True:
                result = supabase.table('students')\
                    .select('main_instructor')\
                    .eq('course_code', course_code)\
                    .range(offset, offset + page_size - 1)\
                    .execute()
                if not result.data:
                    break
                all_records.extend(result.data)
                if len(result.data) < page_size:
                    break
                offset += page_size
            
            # Get unique instructors
            instructors_set = set()
            for record in all_records:
                instructor = record.get('main_instructor', '').strip()
                if instructor:
                    instructors_set.add(instructor)
            
            # Convert to sorted list
            instructors = sorted(list(instructors_set))
            
            return jsonify({'instructors': instructors}), 200
        else:
            return jsonify({'instructors': []}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# ABSENTEE MANAGEMENT API ENDPOINTS
# ============================================

@app.route('/api/absentees/approve', methods=['POST'])
def api_approve_absentees():
    """Approve selected absentee records via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
    try:
        data = request.get_json()
        selected_ids = data.get('ids', [])
        
        if not selected_ids:
            return jsonify({'success': False, 'error': 'No records selected'}), 400
        
        approved_count = 0
        for absentee_id in selected_ids:
            result = supabase.table('absentees').update({
                'status': 'approved',
                'approved_at': datetime.now().isoformat(),
                'approved_by': session.get('username')
            }).eq('id', int(absentee_id)).execute()
            
            if result.data:
                approved_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Approved {approved_count} record(s)',
            'count': approved_count
        }), 200
        
    except Exception as e:
        print(f"Error in api_approve_absentees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/absentees/reject', methods=['POST'])
def api_reject_absentees():
    """Reject selected absentee records via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
    try:
        data = request.get_json()
        selected_ids = data.get('ids', [])
        
        if not selected_ids:
            return jsonify({'success': False, 'error': 'No records selected'}), 400
        
        rejected_count = 0
        for absentee_id in selected_ids:
            result = supabase.table('absentees').update({
                'status': 'rejected',
                'rejected_at': datetime.now().isoformat(),
                'rejected_by': session.get('username')
            }).eq('id', int(absentee_id)).execute()
            
            if result.data:
                rejected_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Rejected {rejected_count} record(s)',
            'count': rejected_count
        }), 200
        
    except Exception as e:
        print(f"Error in api_reject_absentees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/absentees/pending', methods=['POST'])
def api_set_pending_absentees():
    """Set selected absentee records to pending via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
    try:
        data = request.get_json()
        selected_ids = data.get('ids', [])
        
        if not selected_ids:
            return jsonify({'success': False, 'error': 'No records selected'}), 400
        
        pending_count = 0
        for absentee_id in selected_ids:
            result = supabase.table('absentees').update({
                'status': 'pending',
                'approved_at': None,
                'approved_by': None,
                'rejected_at': None,
                'rejected_by': None
            }).eq('id', int(absentee_id)).execute()
            
            if result.data:
                pending_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Set {pending_count} record(s) to pending',
            'count': pending_count
        }), 200
        
    except Exception as e:
        print(f"Error in api_set_pending_absentees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/absentees/delete', methods=['POST'])
def api_delete_absentees():
    """Delete selected absentee records via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
    try:
        data = request.get_json()
        selected_ids = data.get('ids', [])
        
        if not selected_ids:
            return jsonify({'success': False, 'error': 'No records selected'}), 400
        
        deleted_count = 0
        for absentee_id in selected_ids:
            result = supabase.table('absentees').delete().eq('id', int(absentee_id)).execute()
            if result.data:
                deleted_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} record(s)',
            'count': deleted_count
        }), 200
        
    except Exception as e:
        print(f"Error in api_delete_absentees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/absentees/list', methods=['GET'])
def api_list_absentees():
    """Get list of absentees with optional filters via AJAX"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'error': 'Database not configured'}), 500
    
    try:
        # Get filter parameters
        status = request.args.get('status', '')
        exam_date = request.args.get('exam_date', '')
        course_code = request.args.get('course_code', '')
        
        query = supabase.table('absentees').select('*')
        
        if status:
            query = query.eq('status', status)
        if exam_date:
            query = query.eq('exam_date', exam_date)
        if course_code:
            query = query.eq('course_code', course_code)
        
        result = query.order('created_at', desc=True).execute()
        absentees = result.data if result.data else []
        
        # Calculate stats
        all_result = supabase.table('absentees').select('status').execute()
        all_records = all_result.data if all_result.data else []
        stats = {
            'total': len(all_records),
            'pending': len([a for a in all_records if a['status'] == 'pending']),
            'approved': len([a for a in all_records if a['status'] == 'approved']),
            'rejected': len([a for a in all_records if a['status'] == 'rejected'])
        }
        
        return jsonify({
            'success': True,
            'absentees': absentees,
            'stats': stats
        }), 200
        
    except Exception as e:
        print(f"Error in api_list_absentees: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        section = request.form.get('section', 'all')  # Default to 'all' sections
        instructor = request.form.get('instructor', '').strip()  # NEW: Instructor filter
        
        print(f"DEBUG: POST request received with action={action}")
        print(f"program_level={program_level}, semester_id={semester_id}")
        print(f"course_code={course_code},exam_date={exam_date}, section={section}, instructor={instructor}")
        
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
                print(f"DEBUG: Generating preview for {course_code}, section={section}, instructor={instructor}")
                html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True, program_level=program_level, section=section, instructor=instructor)
                    
                if html_content:
                    return html_content
                else:
                    flash(f'Error generating preview: {message}', 'error')
                    
            elif action == 'download' and course_code:
                print(f"DEBUG: Generating download for {course_code}, section={section}, instructor={instructor}")
                # Generate HTML content first
                html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True, in_memory=True, program_level=program_level, section=section, instructor=instructor)
                
                if html_content:
                    # Convert HTML to PDF
                    from app.attendance import html_to_pdf
                    pdf_bytes = html_to_pdf(html_content)
                    
                    if pdf_bytes:
                        # Create a proper filename for download
                        safe_course = secure_filename(str(course_code))
                        safe_date = secure_filename(str(exam_date))
                        section_suffix = f"_{section}" if section and section != 'all' else ""
                        instructor_suffix = f"_{secure_filename(instructor[:20])}" if instructor else ""
                        filename = f"Attendance_{safe_course}{section_suffix}{instructor_suffix}_{safe_date}.pdf"
                        
                        return send_file(
                            BytesIO(pdf_bytes),
                            mimetype='application/pdf',
                            as_attachment=True,
                            download_name=filename
                        )
                    else:
                        flash('Error converting HTML to PDF', 'error')
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
    
    # Initialize session absentees list if not exists
    if 'absentees' not in session:
        session['absentees'] = []
    
    # Get all unique courses from students table
    all_courses = []
    if USE_SUPABASE_DB and supabase:
        try:
            # Handle pagination - Supabase has 1000 record default limit
            all_students = []
            page_size = 1000
            offset = 0
            
            while True:
                response = supabase.table('students').select('course_code, course_title').range(offset, offset + page_size - 1).execute()
                if not response.data:
                    break
                all_students.extend(response.data)
                if len(response.data) < page_size:
                    break
                offset += page_size
            
            if all_students:
                # Create unique set of courses
                unique_courses = {}
                for row in all_students:
                    code = row.get('course_code')
                    title = row.get('course_title')
                    if code and title and code not in unique_courses:
                        unique_courses[code] = title
                # Convert to sorted list of tuples
                all_courses = sorted([(code, title) for code, title in unique_courses.items()])
                print(f"DEBUG: Loaded {len(all_courses)} unique courses for absentee sheet (from {len(all_students)} students)")
        except Exception as e:
            print(f"Error loading courses: {e}")
            flash('Error loading courses from database.', 'error')
    
    # Handle POST actions
    student_info = None
    course_students = None
    selected_course_code = None
    selected_section = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'load_students':
            # Load all students for a selected course
            course_code = request.form.get('course_code', '').strip()
            section = request.form.get('section', '').strip().upper()
            instructor = request.form.get('instructor', '').strip()
            
            if not course_code:
                flash('Please select a course.', 'error')
            elif USE_SUPABASE_DB and supabase:
                try:
                    # Build query with optional filters
                    query = supabase.table('students')\
                        .select('roll_no, name, course_code, course_title, timetable_batch, main_instructor')\
                        .eq('course_code', course_code)
                    
                    # Add section filter if specified
                    if section:
                        query = query.eq('timetable_batch', section)
                    
                    # Add instructor filter if specified
                    if instructor:
                        query = query.eq('main_instructor', instructor)
                    
                    response = query.order('roll_no').execute()
                    
                    if response.data and len(response.data) > 0:
                        course_students = response.data
                        selected_course_code = course_code
                        selected_section = section if section else None
                        filter_msg = f'Loaded {len(course_students)} students from {course_code}'
                        if section:
                            filter_msg += f' (Section: {section})'
                        if instructor:
                            filter_msg += f' (Instructor: {instructor})'
                        flash(filter_msg, 'success')
                    else:
                        flash(f'No students found in course {course_code}' + 
                              (f' section {section}' if section else '') +
                              (f' instructor {instructor}' if instructor else ''), 'error')
                except Exception as e:
                    print(f"Error loading students: {e}")
                    flash('Error loading students from database.', 'error')
        
        elif action == 'add_multiple_absentees':
            # Add multiple selected students to absentee list
            course_code = request.form.get('course_code', '').strip()
            section = request.form.get('section', '').strip().upper()
            selected_students = request.form.getlist('selected_students')
            
            if not selected_students:
                message = 'No students selected.'
                success = False
                added_count = 0
            else:
                added_count = 0
                for student_data in selected_students:
                    # Parse student data (format: "roll_no|name")
                    try:
                        roll_no, name = student_data.split('|', 1)
                        
                        # Get course title from database
                        response = supabase.table('students')\
                            .select('course_title')\
                            .eq('course_code', course_code)\
                            .eq('roll_no', roll_no)\
                            .limit(1)\
                            .execute()
                        
                        course_title = response.data[0]['course_title'] if response.data else ''
                        
                        # Check if student already in list
                        already_added = any(
                            a['roll_no'] == roll_no and a['course_code'] == course_code 
                            for a in session['absentees']
                        )
                        
                        if not already_added:
                            session['absentees'].append({
                                'roll_no': roll_no,
                                'name': name,
                                'course_code': course_code,
                                'course_title': course_title
                            })
                            added_count += 1
                    except Exception as e:
                        print(f"Error processing student {student_data}: {e}")
                
                session.modified = True
                if added_count > 0:
                    message = f'Added {added_count} student(s) to absentee list.'
                    success = True
                else:
                    message = 'All selected students were already in the list.'
                    success = False
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': success,
                    'message': message,
                    'added_count': added_count,
                    'absentees': session['absentees'],
                    'absentees_count': len(session['absentees'])
                })
            else:
                if not selected_students:
                    flash(message, 'warning')
                elif added_count > 0:
                    flash(message, 'success')
                else:
                    flash(message, 'info')
                
                # Reload the student list to show updated view
                selected_course_code = course_code
                selected_section = section if section else None
                try:
                    query = supabase.table('students')\
                        .select('roll_no, name, course_code, course_title, timetable_batch')\
                        .eq('course_code', course_code)
                    if section:
                        query = query.eq('timetable_batch', section)
                    response = query.order('roll_no').execute()
                    if response.data:
                        course_students = response.data
                except Exception as e:
                    print(f"Error reloading students: {e}")
        
        elif action == 'search_student':
            course_code = request.form.get('course_code', '').strip()
            roll_no = request.form.get('roll_no', '').strip().upper()
            
            if not course_code or not roll_no:
                flash('Please select a course and enter roll number.', 'error')
            elif USE_SUPABASE_DB and supabase:
                try:
                    response = supabase.table('students')\
                        .select('roll_no, name, course_code, course_title')\
                        .eq('course_code', course_code)\
                        .eq('roll_no', roll_no)\
                        .execute()
                    
                    if response.data and len(response.data) > 0:
                        row = response.data[0]
                        student_info = {
                            'roll_no': row['roll_no'],
                            'name': row['name'],
                            'course_code': row['course_code'],
                            'course_title': row['course_title']
                        }
                    else:
                        flash(f'Student {roll_no} not found in course {course_code}.', 'error')
                except Exception as e:
                    print(f"Error searching student: {e}")
                    flash('Error searching for student.', 'error')
        
        elif action == 'add_absentee':
            roll_no = request.form.get('roll_no', '').strip()
            name = request.form.get('name', '').strip()
            course_code = request.form.get('course_code', '').strip()
            course_title = request.form.get('course_title', '').strip()
            
            # Check if student already in list
            already_added = any(
                a['roll_no'] == roll_no and a['course_code'] == course_code 
                for a in session['absentees']
            )
            
            if not already_added:
                session['absentees'].append({
                    'roll_no': roll_no,
                    'name': name,
                    'course_code': course_code,
                    'course_title': course_title
                })
                session.modified = True
                message = f'Added {name} ({roll_no}) to absentee list.'
                msg_type = 'success'
            else:
                message = 'Student already in absentee list.'
                msg_type = 'warning'
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': not already_added,
                    'message': message,
                    'absentees': session['absentees'],
                    'absentees_count': len(session['absentees'])
                })
            else:
                flash(message, msg_type)
        
        elif action == 'remove_absentee':
            try:
                index = int(request.form.get('index', -1))
                if 0 <= index < len(session['absentees']):
                    removed = session['absentees'].pop(index)
                    session.modified = True
                    flash(f'Removed {removed["name"]} from list.', 'info')
            except:
                flash('Error removing student.', 'error')
        
        elif action == 'remove_selected':
            # Remove multiple selected absentees
            try:
                selected_indices = request.form.getlist('selected_absentees')
                if selected_indices:
                    # Convert to integers and sort in reverse to avoid index shifting
                    indices = sorted([int(idx) for idx in selected_indices], reverse=True)
                    removed_count = 0
                    for index in indices:
                        if 0 <= index < len(session['absentees']):
                            session['absentees'].pop(index)
                            removed_count += 1
                    session.modified = True
                    message = f'Removed {removed_count} student(s) from absentee list.'
                    success = True
                else:
                    message = 'No students selected for removal.'
                    success = False
                    removed_count = 0
                
                # Return JSON for AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': success,
                        'message': message,
                        'removed_count': removed_count,
                        'absentees': session['absentees'],
                        'absentees_count': len(session['absentees'])
                    })
                else:
                    flash(message, 'success' if success else 'warning')
            except Exception as e:
                print(f"Error removing selected: {e}")
                error_msg = 'Error removing selected students.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
        
        elif action == 'preview_absentees':
            if session['absentees']:
                semester_id = request.form.get('semester_id')
                
                if not semester_id:
                    flash('Please select a semester before previewing.', 'error')
                    return redirect(url_for('mark_absentees'))
                
                # Get exam dates for each course from form
                exam_dates = {}
                for key in request.form.keys():
                    if key.startswith('exam_date_'):
                        course_code = key.replace('exam_date_', '')
                        exam_dates[course_code] = request.form.get(key) or datetime.now().strftime('%Y-%m-%d')
                
                # Group absentees by course code
                absentees_by_course = {}
                for absentee in session['absentees']:
                    course_code = absentee['course_code']
                    if course_code not in absentees_by_course:
                        absentees_by_course[course_code] = []
                    absentees_by_course[course_code].append(absentee['roll_no'])
                
                # Generate attendance sheets for each course with only absentees
                from app.attendance import generate_attendance_sheet
                all_html = []
                
                for course_code, roll_numbers in absentees_by_course.items():
                    exam_date = exam_dates.get(course_code, datetime.now().strftime('%Y-%m-%d'))
                    
                    # Generate attendance sheet with only these specific students
                    html_content, message = generate_attendance_sheet(
                        course_code=course_code,
                        exam_date=exam_date,
                        semester_id=semester_id,
                        preview=True,
                        in_memory=True,
                        program_level=None,
                        section=None,
                        instructor=None,
                        roll_numbers=roll_numbers
                    )
                    
                    if html_content:
                        all_html.append(html_content)
                    else:
                        print(f"Failed to generate attendance sheet for {course_code}: {message}")
                
                if all_html:
                    # Combine all HTML with page breaks
                    combined_html = all_html[0]
                    if len(all_html) > 1:
                        # Insert additional sheets between </body> and </html>
                        for additional_html in all_html[1:]:
                            # Extract body content from additional HTML
                            body_start = additional_html.find('<body>')
                            body_end = additional_html.find('</body>')
                            if body_start != -1 and body_end != -1:
                                body_content = additional_html[body_start + 6:body_end]
                                # Insert before </body> tag of combined HTML
                                insert_pos = combined_html.rfind('</body>')
                                combined_html = combined_html[:insert_pos] + body_content + combined_html[insert_pos:]
                    
                    response = make_response(combined_html)
                    response.headers['Content-Type'] = 'text/html; charset=utf-8'
                    return response
                else:
                    flash('Error generating preview for absentees.', 'error')
            else:
                flash('No absentees to preview.', 'error')
        
        elif action == 'download_absentees':
            print(f"\n{'='*60}")
            print(f"[DOWNLOAD ABSENTEES] Request received")
            print(f"Session absentees count: {len(session.get('absentees', []))}")
            print(f"{'='*60}")
            
            if session['absentees']:
                semester_id = request.form.get('semester_id')
                print(f"[DOWNLOAD ABSENTEES] Semester ID: {semester_id}")
                
                if not semester_id:
                    print("[DOWNLOAD ABSENTEES] ERROR: No semester selected")
                    flash('Please select a semester before downloading.', 'error')
                    return redirect(url_for('mark_absentees'))
                
                # Get exam dates for each course from form
                exam_dates = {}
                for key in request.form.keys():
                    if key.startswith('exam_date_'):
                        course_code = key.replace('exam_date_', '')
                        exam_dates[course_code] = request.form.get(key) or datetime.now().strftime('%Y-%m-%d')
                
                print(f"[DOWNLOAD ABSENTEES] Found {len(exam_dates)} course exam dates")
                for course_code, date in list(exam_dates.items())[:3]:
                    print(f"  - {course_code}: {date}")
                
                # Group absentees by course code
                absentees_by_course = {}
                for absentee in session['absentees']:
                    course_code = absentee['course_code']
                    if course_code not in absentees_by_course:
                        absentees_by_course[course_code] = []
                    absentees_by_course[course_code].append(absentee['roll_no'])
                
                print(f"[DOWNLOAD ABSENTEES] Grouped absentees by course: {list(absentees_by_course.keys())}")
                
                # Generate attendance sheets for each course with only absentees
                from app.attendance import generate_attendance_sheet
                all_pdfs = []
                
                for course_code, roll_numbers in absentees_by_course.items():
                    exam_date = exam_dates.get(course_code, datetime.now().strftime('%Y-%m-%d'))
                    print(f"[DOWNLOAD ABSENTEES] Generating sheet for {course_code} with {len(roll_numbers)} absentee(s), exam_date={exam_date}")
                    
                    try:
                        # Generate attendance sheet with only these specific students
                        html_content, message = generate_attendance_sheet(
                            course_code=course_code,
                            exam_date=exam_date,
                            semester_id=semester_id,
                            preview=True,
                            in_memory=True,
                            program_level=None,
                            section=None,
                            instructor=None,
                            roll_numbers=roll_numbers
                        )
                        
                        print(f"[DOWNLOAD ABSENTEES] HTML generated: {bool(html_content)}, Message: {message}")
                        
                        if html_content:
                            # Convert to PDF
                            print(f"[DOWNLOAD ABSENTEES] Converting {course_code} to PDF...")
                            pdf_bytes = html_to_pdf(html_content)
                            print(f"[DOWNLOAD ABSENTEES] PDF generated: {bool(pdf_bytes)}, Size: {len(pdf_bytes) if pdf_bytes else 0} bytes")
                            
                            if pdf_bytes:
                                all_pdfs.append({
                                    'course_code': course_code,
                                    'exam_date': exam_date,
                                    'pdf': pdf_bytes
                                })
                            else:
                                print(f"[DOWNLOAD ABSENTEES] ERROR: Failed to convert {course_code} to PDF")
                        else:
                            print(f"[DOWNLOAD ABSENTEES] ERROR: Failed to generate attendance sheet for {course_code}: {message}")
                    except Exception as e:
                        print(f"[DOWNLOAD ABSENTEES] EXCEPTION: {type(e).__name__}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                print(f"[DOWNLOAD ABSENTEES] Total PDFs generated: {len(all_pdfs)}")
                
                if not all_pdfs:
                    print("[DOWNLOAD ABSENTEES] ERROR: No PDFs generated")
                    flash('Error generating attendance sheets for absentees.', 'error')
                    return redirect(url_for('mark_absentees'))
                
                # If only one course, send single PDF
                if len(all_pdfs) == 1:
                    pdf_data = all_pdfs[0]
                    filename = f"Absentee_Sheet_{pdf_data['course_code']}_{pdf_data['exam_date']}.pdf"
                    print(f"[DOWNLOAD ABSENTEES] Sending single PDF: {filename}")
                    
                    return send_file(
                        BytesIO(pdf_data['pdf']),
                        mimetype='application/pdf',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    # Multiple courses - create a ZIP file
                    print(f"[DOWNLOAD ABSENTEES] Creating ZIP with {len(all_pdfs)} PDFs")
                    import zipfile
                    zip_buffer = BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for pdf_data in all_pdfs:
                            filename = f"Absentee_Sheet_{pdf_data['course_code']}_{pdf_data['exam_date']}.pdf"
                            zip_file.writestr(filename, pdf_data['pdf'])
                            print(f"[DOWNLOAD ABSENTEES]   Added to ZIP: {filename}")
                    
                    zip_buffer.seek(0)
                    today = datetime.now().strftime('%Y-%m-%d')
                    zip_filename = f"Absentee_Sheets_{today}.zip"
                    print(f"[DOWNLOAD ABSENTEES] Sending ZIP: {zip_filename}, Size: {len(zip_buffer.getvalue())} bytes")
                    
                    return send_file(
                        zip_buffer,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=zip_filename
                    )
            else:
                flash('No absentees to download.', 'error')
        
        elif action == 'upload_to_admin':
            # Staff uploads absentees to admin for consolidation
            if session['absentees']:
                semester_id = request.form.get('semester_id')
                
                # Get exam dates for each course from form
                exam_dates = {}
                for key in request.form.keys():
                    if key.startswith('exam_date_'):
                        course_code = key.replace('exam_date_', '')
                        exam_dates[course_code] = request.form.get(key) or datetime.now().strftime('%Y-%m-%d')
                
                if USE_SUPABASE_DB and supabase:
                    try:
                        marked_by = session.get('username', 'unknown')
                        
                        # Generate a unique batch ID for this upload
                        batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
                        
                        # Insert each absentee into the absentees table with course-specific exam dates
                        absentees_data = []
                        for absentee in session['absentees']:
                            course_code = absentee['course_code']
                            exam_date = exam_dates.get(course_code, datetime.now().strftime('%Y-%m-%d'))
                            
                            absentees_data.append({
                                'roll_no': absentee['roll_no'],
                                'name': absentee['name'],
                                'course_code': absentee['course_code'],
                                'course_title': absentee['course_title'],
                                'exam_date': exam_date,
                                'semester_id': int(semester_id) if semester_id else None,
                                'marked_by': marked_by,
                                'status': 'pending',
                                'storage_filename': f"{exam_date}_{absentee['course_code']}_{marked_by}_{batch_id}.json"
                            })
                        
                        # Batch insert to database
                        result = supabase.table('absentees').insert(absentees_data).execute()
                        
                        if result.data:
                            # Also upload to pending_absentee bucket
                            # Group by course for storage
                            for course_code in exam_dates.keys():
                                course_absentees = [a for a in session['absentees'] if a['course_code'] == course_code]
                                if course_absentees:
                                    success, filename, msg = absentee_storage.upload_pending_absentees(
                                        course_absentees,
                                        marked_by,
                                        exam_dates[course_code]
                                    )
                                    if success:
                                        print(f"[DEBUG] Stored {course_code} in pending_absentee bucket: {filename}")
                                    else:
                                        print(f"[DEBUG] Storage bucket upload failed for {course_code}: {msg}")
                            
                            count = len(session['absentees'])
                            courses_count = len(set(a['course_code'] for a in session['absentees']))
                            flash(f'Successfully uploaded {count} absentees across {courses_count} course(s) to admin!', 'success')
                            # Clear the session list after successful upload
                            session['absentees'] = []
                            session.modified = True
                        else:
                            flash('Failed to upload absentees. Please try again.', 'error')
                    except Exception as e:
                        print(f"Error uploading absentees: {e}")
                        flash(f'Error uploading absentees: {str(e)}', 'error')
                else:
                    flash('Database not configured. Please contact administrator.', 'error')
            else:
                flash('No absentees to upload.', 'error')
        
        elif action == 'clear_absentees':
            count = len(session['absentees'])
            session['absentees'] = []
            session.modified = True
            message = f'Cleared {count} absentee(s).'
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': message,
                    'absentees_count': 0
                })
            else:
                flash(message, 'info')
    
    # Prepare course info for display
    course_info = None
    absentees_by_course = {}
    
    if session['absentees']:
        first_absentee = session['absentees'][0]
        course_info = {
            'course_code': first_absentee['course_code'],
            'course_title': first_absentee['course_title']
        }
        
        # Group absentees by course for easier display
        for idx, absentee in enumerate(session['absentees']):
            course_code = absentee['course_code']
            if course_code not in absentees_by_course:
                absentees_by_course[course_code] = {
                    'course_title': absentee['course_title'],
                    'students': []
                }
            absentees_by_course[course_code]['students'].append({
                'roll_no': absentee['roll_no'],
                'name': absentee['name'],
                'index': idx  # Original index for removal
            })
    
    # Get semesters for the upload form
    semesters = get_all_semesters()
    
    return render_template('absentee.html',
                         all_courses=all_courses,
                         absentees=session['absentees'],
                         absentees_by_course=absentees_by_course,
                         course_info=course_info,
                         student_info=student_info,
                         course_students=course_students,
                         selected_course_code=selected_course_code,
                         selected_section=selected_section,
                         semesters=semesters)


@app.route('/admin/absentees', methods=['GET', 'POST'])
def admin_absentees():
    """Admin page to view and consolidate all uploaded absentees"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Only admin can access this page
    if session.get('role') != 'admin':
        flash('Access denied. Only administrators can access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    if not USE_SUPABASE_DB or not supabase:
        flash('Database not configured.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get filter parameters
    filter_date = request.args.get('exam_date', '')
    filter_status = request.args.get('status', '')  # Empty = show all by default
    filter_course = request.args.get('course_code', '')
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        print(f"[DEBUG] POST received - action: {action}")
        print(f"[DEBUG] Form data: {dict(request.form)}")
        
        if action == 'approve_selected':
            selected_ids = request.form.getlist('selected_absentees')
            print(f"[DEBUG] Approve action - selected_ids: {selected_ids}")
            if selected_ids:
                try:
                    approved_records = []
                    for absentee_id in selected_ids:
                        print(f"[DEBUG] Approving absentee id: {absentee_id}")
                        # First get the record to save to bucket
                        record = supabase.table('absentees').select('*').eq('id', int(absentee_id)).execute()
                        if record.data:
                            approved_records.append(record.data[0])
                        
                        # Update status in database
                        result = supabase.table('absentees').update({
                            'status': 'approved',
                            'approved_at': datetime.now().isoformat(),
                            'approved_by': session.get('username')
                        }).eq('id', int(absentee_id)).execute()
                        print(f"[DEBUG] Update result: {result.data}")
                    
                    # Upload approved records to approved_absentee bucket
                    if approved_records:
                        import json
                        exam_date = approved_records[0].get('exam_date', datetime.now().strftime('%Y-%m-%d'))
                        course_codes = list(set(r.get('course_code', 'UNKNOWN') for r in approved_records))
                        filename = f"{exam_date}_approved_{datetime.now().strftime('%H%M%S')}.json"
                        
                        content = json.dumps({
                            'exam_date': exam_date,
                            'approved_by': session.get('username'),
                            'approved_at': datetime.now().isoformat(),
                            'courses': course_codes,
                            'absentees': [{
                                'roll_no': r['roll_no'],
                                'name': r['name'],
                                'course_code': r['course_code'],
                                'course_title': r.get('course_title', ''),
                                'marked_by': r.get('marked_by', '')
                            } for r in approved_records]
                        }, indent=2)
                        
                        try:
                            from helpers.supabase_storage import APPROVED_ABSENTEE_BUCKET
                            result = absentee_storage.client.storage.from_(APPROVED_ABSENTEE_BUCKET).upload(
                                filename,
                                content.encode('utf-8'),
                                file_options={"content-type": "application/json"}
                            )
                            print(f"[DEBUG] Uploaded to approved bucket: {filename}")
                        except Exception as e:
                            print(f"[DEBUG] Error uploading to approved bucket: {e}")
                    
                    flash(f'Approved {len(selected_ids)} absentee records.', 'success')
                    # Redirect to show approved records
                    return redirect(url_for('admin_absentees', status='approved'))
                except Exception as e:
                    print(f"Error approving absentees: {e}")
                    flash(f'Error approving absentees: {str(e)}', 'error')
                    return redirect(url_for('admin_absentees'))
            else:
                flash('No records selected.', 'warning')
                return redirect(url_for('admin_absentees'))
        
        elif action == 'reject_selected':
            selected_ids = request.form.getlist('selected_absentees')
            print(f"[DEBUG] Reject action - selected_ids: {selected_ids}")
            if selected_ids:
                try:
                    rejected_records = []
                    for absentee_id in selected_ids:
                        print(f"[DEBUG] Rejecting absentee id: {absentee_id}")
                        # First get the record to save to bucket
                        record = supabase.table('absentees').select('*').eq('id', int(absentee_id)).execute()
                        if record.data:
                            rejected_records.append(record.data[0])
                        
                        # Update status in database with rejected fields
                        result = supabase.table('absentees').update({
                            'status': 'rejected',
                            'rejected_at': datetime.now().isoformat(),
                            'rejected_by': session.get('username')
                        }).eq('id', int(absentee_id)).execute()
                        print(f"[DEBUG] Reject update result: {result.data}")
                    
                    # Upload rejected records to rejected_absentee bucket
                    if rejected_records:
                        import json
                        exam_date = rejected_records[0].get('exam_date', datetime.now().strftime('%Y-%m-%d'))
                        filename = f"{exam_date}_rejected_{datetime.now().strftime('%H%M%S')}.json"
                        
                        content = json.dumps({
                            'exam_date': exam_date,
                            'rejected_by': session.get('username'),
                            'rejected_at': datetime.now().isoformat(),
                            'absentees': [{
                                'roll_no': r['roll_no'],
                                'name': r['name'],
                                'course_code': r['course_code'],
                                'course_title': r.get('course_title', ''),
                                'marked_by': r.get('marked_by', '')
                            } for r in rejected_records]
                        }, indent=2)
                        
                        try:
                            from helpers.supabase_storage import REJECTED_ABSENTEE_BUCKET
                            result = absentee_storage.client.storage.from_(REJECTED_ABSENTEE_BUCKET).upload(
                                filename,
                                content.encode('utf-8'),
                                file_options={"content-type": "application/json"}
                            )
                            print(f"[DEBUG] Uploaded to rejected bucket: {filename}")
                        except Exception as e:
                            print(f"[DEBUG] Error uploading to rejected bucket: {e}")
                    
                    flash(f'Rejected {len(selected_ids)} absentee records.', 'info')
                    # Redirect to show rejected records
                    return redirect(url_for('admin_absentees', status='rejected'))
                except Exception as e:
                    print(f"Error rejecting absentees: {e}")
                    flash(f'Error rejecting absentees: {str(e)}', 'error')
                    return redirect(url_for('admin_absentees'))
            else:
                flash('No records selected.', 'warning')
                return redirect(url_for('admin_absentees'))
        
        elif action == 'pending_selected':
            selected_ids = request.form.getlist('selected_absentees')
            print(f"[DEBUG] Pending action - selected_ids: {selected_ids}")
            if selected_ids:
                try:
                    for absentee_id in selected_ids:
                        print(f"[DEBUG] Setting pending for absentee id: {absentee_id}")
                        # Reset status to pending and clear approval/rejection fields
                        result = supabase.table('absentees').update({
                            'status': 'pending',
                            'approved_at': None,
                            'approved_by': None,
                            'rejected_at': None,
                            'rejected_by': None
                        }).eq('id', int(absentee_id)).execute()
                        print(f"[DEBUG] Pending update result: {result.data}")
                    
                    flash(f'Set {len(selected_ids)} absentee records to pending.', 'info')
                    return redirect(url_for('admin_absentees', status='pending'))
                except Exception as e:
                    print(f"Error setting absentees to pending: {e}")
                    flash(f'Error setting absentees to pending: {str(e)}', 'error')
                    return redirect(url_for('admin_absentees'))
            else:
                flash('No records selected.', 'warning')
                return redirect(url_for('admin_absentees'))
        
        elif action == 'delete_selected':
            selected_ids = request.form.getlist('selected_absentees')
            if selected_ids:
                try:
                    for absentee_id in selected_ids:
                        supabase.table('absentees').delete().eq('id', int(absentee_id)).execute()
                    flash(f'Deleted {len(selected_ids)} absentee records.', 'info')
                    # Redirect to refresh the page
                    return redirect(url_for('admin_absentees'))
                except Exception as e:
                    print(f"Error deleting absentees: {e}")
                    flash(f'Error deleting absentees: {str(e)}', 'error')
                    return redirect(url_for('admin_absentees'))
            else:
                flash('No records selected.', 'warning')
                return redirect(url_for('admin_absentees'))
        
        elif action == 'preview_consolidated':
            # Show ALL approved absentees (no date filter)
            try:
                # Get all approved absentees with semester info joined
                result = supabase.table('absentees')\
                    .select('*, semesters(academic_year, semester_type, exam_type)')\
                    .eq('status', 'approved')\
                    .execute()
                
                # Enrich with instructor data and flatten semester info
                if result.data:
                    for absentee in result.data:
                        # Ensure exam_date is properly formatted as string
                        exam_date = absentee.get('exam_date')
                        if exam_date:
                            if hasattr(exam_date, 'strftime'):
                                absentee['exam_date'] = exam_date.strftime('%Y-%m-%d')
                            elif isinstance(exam_date, str):
                                absentee['exam_date'] = str(exam_date).split('T')[0] if 'T' in str(exam_date) else str(exam_date)
                        
                        # Flatten semester data
                        if absentee.get('semesters'):
                            absentee['academic_year'] = absentee['semesters'].get('academic_year', '')
                            absentee['semester_type'] = absentee['semesters'].get('semester_type', '')
                            absentee['exam_type'] = absentee['semesters'].get('exam_type', '')
                        else:
                            absentee['academic_year'] = ''
                            absentee['semester_type'] = ''
                            absentee['exam_type'] = ''
                        
                        # Get instructor from students table
                        student_query = supabase.table('students')\
                            .select('main_instructor')\
                            .eq('course_code', absentee['course_code'])\
                            .limit(1)\
                            .execute()
                        if student_query.data:
                            absentee['instructor'] = student_query.data[0].get('main_instructor', 'N/A')
                        else:
                            absentee['instructor'] = 'N/A'
                
                if result.data:
                    # Generate consolidated HTML for preview (not download)
                    html_content = generate_consolidated_absentee_html(result.data)
                    return html_content
                else:
                    # Return a simple HTML page with error message for the new tab
                    date_info = "(no approved absentees in the system)"
                    return f"""<!DOCTYPE html>
<html>
<head>
    <title>No Absentees Found</title>
    <style>
        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
        .message {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h2 {{ color: #f59e0b; margin-bottom: 10px; }}
        p {{ color: #6b7280; }}
        a {{ color: #3b82f6; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="message">
        <h2>⚠️ No Approved Absentees Found</h2>
        <p>There are no approved absentees {date_info}</p>
        <p>Please approve some absentees first or try a different date.</p>
        <p><a href="javascript:window.close()">Close this tab</a></p>
    </div>
</body>
</html>"""
            except Exception as e:
                print(f"Error previewing consolidated absentees: {e}")
                # Return a simple HTML page with error message for the new tab
                return f"""<!DOCTYPE html>
<html>
<head>
    <title>Preview Error</title>
    <style>
        body {{ font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
        .message {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h2 {{ color: #ef4444; margin-bottom: 10px; }}
        p {{ color: #6b7280; }}
        a {{ color: #3b82f6; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="message">
        <h2>❌ Error Generating Preview</h2>
        <p>An error occurred while generating the consolidated absentee list.</p>
        <p>Error: {str(e)}</p>
        <p><a href="javascript:window.close()">Close this tab</a></p>
    </div>
</body>
</html>"""
        
        elif action == 'download_consolidated':
            # Download ALL approved absentees (no date filter)
            try:
                # Get all approved absentees with semester info joined
                result = supabase.table('absentees')\
                    .select('*, semesters(academic_year, semester_type, exam_type)')\
                    .eq('status', 'approved')\
                    .execute()
                
                # Enrich with instructor data and flatten semester info
                if result.data:
                    for absentee in result.data:
                        # Ensure exam_date is properly formatted as string
                        exam_date = absentee.get('exam_date')
                        if exam_date:
                            if hasattr(exam_date, 'strftime'):
                                absentee['exam_date'] = exam_date.strftime('%Y-%m-%d')
                            elif isinstance(exam_date, str):
                                absentee['exam_date'] = str(exam_date).split('T')[0] if 'T' in str(exam_date) else str(exam_date)
                        
                        # Flatten semester data
                        if absentee.get('semesters'):
                            absentee['academic_year'] = absentee['semesters'].get('academic_year', '')
                            absentee['semester_type'] = absentee['semesters'].get('semester_type', '')
                            absentee['exam_type'] = absentee['semesters'].get('exam_type', '')
                        else:
                            absentee['academic_year'] = ''
                            absentee['semester_type'] = ''
                            absentee['exam_type'] = ''
                        
                        # Get instructor from students table
                        student_query = supabase.table('students')\
                            .select('main_instructor')\
                            .eq('course_code', absentee['course_code'])\
                            .limit(1)\
                            .execute()
                        if student_query.data:
                            absentee['instructor'] = student_query.data[0].get('main_instructor', 'N/A')
                        else:
                            absentee['instructor'] = 'N/A'
                    
                    # Generate consolidated HTML
                    try:
                        html_content = generate_consolidated_absentee_html(result.data)
                    except Exception as html_err:
                        print(f"Error in generate_consolidated_absentee_html: {html_err}")
                        import traceback
                        traceback.print_exc()
                        flash(f'Error generating HTML: {str(html_err)}', 'error')
                        return redirect(url_for('view_absentees'))
                    
                    # Return as HTML (no PDF conversion)
                    filename = f"Consolidated_Absentees_{datetime.now().strftime('%Y-%m-%d')}.html"
                    
                    return send_file(
                        BytesIO(html_content.encode('utf-8')),
                        mimetype='text/html',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    flash('No approved absentees found.', 'warning')
            except Exception as e:
                print(f"Error downloading consolidated absentees: {e}")
                flash('Error generating consolidated report.', 'error')
        
        elif action == 'download_approved_only':
            # Download only approved absentees from database
            try:
                # Join with semesters table to get full semester info
                result = supabase.table('absentees')\
                    .select('*, semesters(academic_year, semester_type, exam_type)')\
                    .eq('status', 'approved')\
                    .execute()
                if result.data:
                    # Enrich with instructor data and flatten semester info
                    for absentee in result.data:
                        # Ensure exam_date is properly formatted as string
                        exam_date = absentee.get('exam_date')
                        if exam_date:
                            # Convert to string if it's not already (handles date objects)
                            if hasattr(exam_date, 'strftime'):
                                absentee['exam_date'] = exam_date.strftime('%Y-%m-%d')
                            elif isinstance(exam_date, str):
                                # If it's already a string, ensure it's in the right format
                                # PostgreSQL DATE fields come as ISO format strings (YYYY-MM-DD)
                                absentee['exam_date'] = str(exam_date).split('T')[0] if 'T' in str(exam_date) else str(exam_date)
                        
                        # Flatten semester data
                        if absentee.get('semesters'):
                            absentee['academic_year'] = absentee['semesters'].get('academic_year', '')
                            absentee['semester_type'] = absentee['semesters'].get('semester_type', '')
                            absentee['exam_type'] = absentee['semesters'].get('exam_type', '')
                        else:
                            absentee['academic_year'] = ''
                            absentee['semester_type'] = ''
                            absentee['exam_type'] = ''
                        
                        # Get instructor data
                        student_query = supabase.table('students')\
                            .select('main_instructor')\
                            .eq('course_code', absentee.get('course_code', ''))\
                            .limit(1)\
                            .execute()
                        if student_query.data:
                            absentee['instructor'] = student_query.data[0].get('main_instructor', 'N/A')
                        else:
                            absentee['instructor'] = 'N/A'
                    
                    # Generate HTML for approved absentees 
                    try:
                        html_content = generate_consolidated_absentee_html(result.data)
                        
                        # Save HTML for debugging
                        try:
                            with open('debug_approved_absentees.html', 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            print(f"[DEBUG] Saved HTML to debug_approved_absentees.html ({len(html_content)} chars)")
                        except Exception as e:
                            print(f"[DEBUG] Could not save HTML: {e}")
                    except Exception as html_err:
                        print(f"Error in generate_consolidated_absentee_html: {html_err}")
                        import traceback
                        traceback.print_exc()
                        flash(f'Error generating HTML: {str(html_err)}', 'error')
                        return redirect(url_for('view_absentees'))
                    
                    # Return as HTML (no PDF conversion)
                    filename = f"Approved_Absentees_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.html"
                    
                    return send_file(
                        BytesIO(html_content.encode('utf-8')),
                        mimetype='text/html',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    flash('No approved absentees found.', 'warning')
            except Exception as e:
                print(f"Error downloading approved absentees: {e}")
                import traceback
                traceback.print_exc()
                flash('Error generating approved absentees report.', 'error')
        
        elif action == 'download_from_storage':
            # Download consolidated absentees from approved_absentee bucket
            exam_date = request.form.get('exam_date', '')
            try:
                absentees_from_storage = absentee_storage.get_approved_absentees_data(exam_date if exam_date else None)
                
                if absentees_from_storage:
                    # Enrich with instructor data and semester info from students table
                    for absentee in absentees_from_storage:
                        course_code = absentee.get('course_code', '')
                        roll_no = absentee.get('roll_no', '')
                        
                        # Get instructor and semester info from students table
                        if roll_no and course_code:
                            student_query = supabase.table('students')\
                                .select('main_instructor, semester_id, semesters(academic_year, semester_type, exam_type)')\
                                .eq('roll_no', roll_no)\
                                .eq('course_code', course_code)\
                                .limit(1)\
                                .execute()
                            if student_query.data and len(student_query.data) > 0:
                                student_data = student_query.data[0]
                                absentee['instructor'] = student_data.get('main_instructor', 'N/A')
                                # Flatten semester data
                                if student_data.get('semesters'):
                                    absentee['academic_year'] = student_data['semesters'].get('academic_year', '')
                                    absentee['semester_type'] = student_data['semesters'].get('semester_type', '')
                                    absentee['exam_type'] = student_data['semesters'].get('exam_type', '')
                                else:
                                    absentee['academic_year'] = ''
                                    absentee['semester_type'] = ''
                                    absentee['exam_type'] = ''
                            else:
                                absentee['instructor'] = 'N/A'
                                absentee['academic_year'] = ''
                                absentee['semester_type'] = ''
                                absentee['exam_type'] = ''
                        else:
                            absentee['instructor'] = 'N/A'
                            absentee['academic_year'] = ''
                            absentee['semester_type'] = ''
                            absentee['exam_type'] = ''
                    
                    # Generate HTML for storage absentees
                    try:
                        html_content = generate_consolidated_absentee_html(absentees_from_storage)
                    except Exception as html_err:
                        print(f"Error in generate_consolidated_absentee_html: {html_err}")
                        import traceback
                        traceback.print_exc()
                        flash(f'Error generating HTML: {str(html_err)}', 'error')
                        return redirect(url_for('view_absentees'))
                    
                    # Return as HTML (no PDF conversion)
                    filename = f"Storage_Absentees_{exam_date or 'all'}.html"
                    
                    return send_file(
                        BytesIO(html_content.encode('utf-8')),
                        mimetype='text/html',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    flash('No approved absentees found in storage.', 'warning')
            except Exception as e:
                print(f"Error downloading from storage: {e}")
                flash(f'Error downloading from storage: {str(e)}', 'error')
        
        elif action == 'list_storage_files':
            # List all files in storage buckets (for debugging/admin view)
            try:
                pending_files = absentee_storage.list_pending_absentees()
                approved_files = absentee_storage.list_approved_absentees()
                rejected_files = absentee_storage.list_rejected_absentees()
                
                flash(f'Storage: {len(pending_files)} pending, {len(approved_files)} approved, {len(rejected_files)} rejected files.', 'info')
            except Exception as e:
                print(f"Error listing storage files: {e}")
                flash(f'Error listing storage files: {str(e)}', 'error')
    
    # Fetch absentees based on filters
    try:
        # Fetch ALL absentees once for stats and unique values
        all_data_result = supabase.table('absentees').select('*').execute()
        all_records = all_data_result.data if all_data_result.data else []
        
        # Compute statistics from ALL records
        stats = {
            'total': len(all_records),
            'pending': len([a for a in all_records if a['status'] == 'pending']),
            'approved': len([a for a in all_records if a['status'] == 'approved']),
            'rejected': len([a for a in all_records if a['status'] == 'rejected'])
        }
        
        # Get unique dates and courses from ALL records
        unique_dates = sorted(set(row['exam_date'] for row in all_records)) if all_records else []
        unique_courses = sorted(set(row['course_code'] for row in all_records)) if all_records else []
        
        # Filter records for display
        absentees_list = all_records
        if filter_status:
            absentees_list = [a for a in absentees_list if a['status'] == filter_status]
        if filter_date:
            absentees_list = [a for a in absentees_list if a['exam_date'] == filter_date]
        if filter_course:
            absentees_list = [a for a in absentees_list if a['course_code'] == filter_course]
        
        # Sort by creation date
        absentees_list = sorted(absentees_list, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Get all unique emails/usernames from filtered absentees for batch lookup
        unique_marked_by = list(set(a.get('marked_by', 'unknown') for a in absentees_list))
        # Remove 'unknown' from the list to avoid unnecessary queries
        unique_marked_by = [m for m in unique_marked_by if m != 'unknown']
        
        # Batch fetch staff names from users table (marked_by contains email)
        email_to_name = {}
        if unique_marked_by:
            try:
                users_result = supabase.table('users').select('email, full_name').in_('email', unique_marked_by).execute()
                if users_result.data:
                    email_to_name = {u['email']: u['full_name'] for u in users_result.data}
            except Exception as e:
                print(f"Error fetching user names: {e}")
        
        # Enrich absentees with staff names and formatted dates
        for absentee in absentees_list:
            marked_by_email = absentee.get('marked_by', 'unknown')
            absentee['marked_by_name'] = email_to_name.get(marked_by_email, marked_by_email)
            
            # Format exam_date to dd/mm/yyyy
            exam_date = absentee.get('exam_date', '')
            try:
                date_obj = datetime.strptime(exam_date, '%Y-%m-%d')
                absentee['exam_date_formatted'] = date_obj.strftime('%d/%m/%Y')
            except:
                absentee['exam_date_formatted'] = exam_date
        
        # Get storage bucket file counts
        try:
            storage_stats = {
                'pending_files': len(absentee_storage.list_pending_absentees()),
                'approved_files': len(absentee_storage.list_approved_absentees()),
                'rejected_files': len(absentee_storage.list_rejected_absentees())
            }
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            storage_stats = {'pending_files': 0, 'approved_files': 0, 'rejected_files': 0}
        
    except Exception as e:
        print(f"Error fetching absentees: {e}")
        absentees_list = []
        unique_dates = []
        unique_courses = []
        stats = {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0}
        storage_stats = {'pending_files': 0, 'approved_files': 0, 'rejected_files': 0}
    
    return render_template('admin_absentees.html',
                         absentees=absentees_list,
                         unique_dates=unique_dates,
                         unique_courses=unique_courses,
                         filter_date=filter_date,
                         filter_status=filter_status,
                         filter_course=filter_course,
                         stats=stats,
                         storage_stats=storage_stats)


@app.route('/clear_bucket/<bucket_type>', methods=['POST'])
def clear_bucket(bucket_type):
    """Clear all files from a specific bucket"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Only admin can clear buckets
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Access denied. Only administrators can clear buckets.'}), 403
    
    if not USE_SUPABASE_DB or not supabase:
        return jsonify({'success': False, 'message': 'Database not configured.'}), 500
    
    # Validate bucket type
    valid_buckets = ['pending', 'approved', 'rejected', 'all']
    if bucket_type not in valid_buckets:
        return jsonify({'success': False, 'message': f'Invalid bucket type. Must be one of: {", ".join(valid_buckets)}'}), 400
    
    try:
        results = {}
        
        if bucket_type == 'all':
            # Clear all absentee buckets
            results = absentee_storage.clear_all_absentee_buckets()
            total_deleted = sum(r[2] for r in results.values())
            
            return jsonify({
                'success': True,
                'message': f'Successfully cleared all absentee buckets. Total files deleted: {total_deleted}',
                'details': {
                    'pending': {'count': results['pending'][2], 'message': results['pending'][1]},
                    'approved': {'count': results['approved'][2], 'message': results['approved'][1]},
                    'rejected': {'count': results['rejected'][2], 'message': results['rejected'][1]}
                }
            })
        else:
            # Clear specific bucket
            if bucket_type == 'pending':
                success, message, count = absentee_storage.clear_pending_bucket()
            elif bucket_type == 'approved':
                success, message, count = absentee_storage.clear_approved_bucket()
            elif bucket_type == 'rejected':
                success, message, count = absentee_storage.clear_rejected_bucket()
            
            if success:
                return jsonify({'success': True, 'message': message, 'deleted_count': count})
            else:
                return jsonify({'success': False, 'message': message}), 500
                
    except Exception as e:
        print(f"Error clearing bucket: {e}")
        return jsonify({'success': False, 'message': f'Error clearing bucket: {str(e)}'}), 500


@app.route('/clear_bucket_page', methods=['GET', 'POST'])
def clear_bucket_page():
    """Admin page to clear storage buckets"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Only admin can access this page
    if session.get('role') != 'admin':
        flash('Access denied. Only administrators can access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Handle POST actions
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'clear_pending':
            success, message, count = absentee_storage.clear_pending_bucket()
            flash(message, 'success' if success else 'error')
        elif action == 'clear_approved':
            success, message, count = absentee_storage.clear_approved_bucket()
            flash(message, 'success' if success else 'error')
        elif action == 'clear_rejected':
            success, message, count = absentee_storage.clear_rejected_bucket()
            flash(message, 'success' if success else 'error')
        elif action == 'clear_all':
            results = absentee_storage.clear_all_absentee_buckets()
            total_deleted = sum(r[2] for r in results.values())
            flash(f'Cleared all buckets. Total files deleted: {total_deleted}', 'success')
        
        return redirect(url_for('admin_absentees'))
    
    # For GET, redirect to admin absentees page
    return redirect(url_for('admin_absentees'))


def generate_consolidated_absentee_html(absentees):
    """Generate HTML for consolidated absentee sheet with new format"""
    from helpers.utils import sort_by_roll_number
    from collections import defaultdict
    
    if not absentees or len(absentees) == 0:
        return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>No Absentees</title></head>
<body><p>No absentees found.</p></body></html>"""
    
    # Group by course code and course name
    grouped = defaultdict(list)
    for absentee in absentees:
        key = (
            absentee.get('course_code', ''),
            absentee.get('course_title', '')
        )
        grouped[key].append(absentee)
    
    # Sort courses by course code
    sorted_courses = sorted(grouped.items(), key=lambda x: x[0][0])
    
    # Flatten all absentees and sort them: first by course, then alphabetically by student name
    all_sorted_absentees = []
    for (course_code, course_title), course_absentees in sorted_courses:
        # Sort students alphabetically by name within each course
        sorted_students = sorted(course_absentees, key=lambda x: x.get('name', '').strip().upper())
        all_sorted_absentees.extend([(course_code, course_title, student) for student in sorted_students])
    
    # Start HTML with new format
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Consolidated Absentee Sheet</title>
    <style>
        @page {
            size: A4;
            margin: 15mm;
        }
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            padding: 0;
        }
        .header { 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .college-name { 
            font-weight: bold; 
            font-size: 16px;
            margin-bottom: 5px;
        }
        .department { 
            font-weight: bold; 
            font-size: 14px;
            margin-bottom: 5px;
        }
        .sheet-title { 
            font-weight: bold; 
            font-size: 14px;
            margin-top: 10px;
            text-decoration: underline;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
        }
        th, td { 
            border: 1px solid black; 
            padding: 8px; 
            text-align: left; 
            font-size: 11px;
        }
        th { 
            background-color: #f0f0f0; 
            font-weight: bold;
            text-align: center;
        }
        .signature-line {
            margin-top: 60px;
            margin-bottom: 20px;
            border-top: 1px solid black;
            width: 250px;
            text-align: center;
            padding-top: 5px;
            font-size: 12px;
        }
        @media print {
            body { 
                margin: 10mm; 
            }
            .page-break {
                page-break-after: always;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="college-name">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
        <div class="department">DEPARTMENT OF MECHANICAL ENGINEERING</div>
        <div class="sheet-title">Consolidated Absentee Sheet</div>
    </div>

    <!-- Absentees Table -->
    <table>
        <thead>
            <tr>
                <th style="width: 5%;">Si.No</th>
                <th style="width: 12%;">Roll No</th>
                <th style="width: 20%;">Student Name</th>
                <th style="width: 10%;">Course Code</th>
                <th style="width: 25%;">Course Name</th>
                <th style="width: 12%;">Exam Date</th>
                <th style="width: 16%;">Instructor</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # Add all absentee rows
    for idx, (course_code, course_title, student) in enumerate(all_sorted_absentees, 1):
        roll_no = student.get('roll_no', '')
        name = student.get('name', '')
        exam_date = student.get('exam_date', '')
        instructor = student.get('instructor', 'N/A')
        
        # Format exam date
        try:
            formatted_exam_date = datetime.strptime(str(exam_date), '%Y-%m-%d').strftime('%d-%m-%Y')
        except Exception as e:
            formatted_exam_date = str(exam_date) if exam_date else ''
        
        html_content += f"""
            <tr>
                <td style="text-align: center;">{idx}</td>
                <td>{roll_no}</td>
                <td>{name}</td>
                <td>{course_code}</td>
                <td>{course_title}</td>
                <td style="text-align: center;">{formatted_exam_date}</td>
                <td>{instructor}</td>
            </tr>
"""
    
    html_content += """
        </tbody>
    </table>

    <!-- HOD Signature -->
    <div class="signature-line">
        Signature of HOD
    </div>
</body>
</html>
"""
    
    return html_content

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
                <th style="width: 50px;">S.No</th>
                <th style="width: 120px;">Roll Number</th>
                <th style="width: 250px;">Student Name</th>
                <th style="width: 100px;">Course Code</th>
                <th style="width: 300px;">Course Name</th>
                <th style="width: 110px;">Date of Exam</th>
            </tr>
        </thead>
        <tbody>
"""
    
    formatted_exam_date = datetime.strptime(exam_date, '%Y-%m-%d').strftime('%d-%m-%Y')
    for idx, student in enumerate(sorted_absentees, 1):
        html += f"""            <tr>
                <td>{idx}</td>
                <td>{student['roll_no']}</td>
                <td>{student['name']}</td>
                <td>{course_code}</td>
                <td>{course_title}</td>
                <td>{formatted_exam_date}</td>
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


def generate_absentee_html_by_course(absentees, exam_dates):
    """Generate HTML for absentee list grouped by course with individual exam dates"""
    if not absentees:
        return ""
    
    # Sort absentees by roll number
    from helpers.utils import sort_by_roll_number
    absentees_tuples = [(a['roll_no'], a['name'], a['course_code'], a['course_title']) for a in absentees]
    sorted_absentees_tuples = sort_by_roll_number(absentees_tuples)
    sorted_absentees = [
        {'roll_no': t[0], 'name': t[1], 'course_code': t[2], 'course_title': t[3]}
        for t in sorted_absentees_tuples
    ]
    
    # Collect all exam dates
    student_data = []
    for absentee in sorted_absentees:
        course_code = absentee['course_code']
        exam_date = exam_dates.get(course_code, datetime.now().strftime('%Y-%m-%d'))
        try:
            formatted_exam_date = datetime.strptime(exam_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            formatted_exam_date = exam_date
        
        student_data.append({
            'roll_no': absentee['roll_no'],
            'name': absentee['name'],
            'course_code': course_code,
            'course_title': absentee['course_title'],
            'exam_date': formatted_exam_date
        })
    
    # Count unique courses
    unique_courses = len(set(s['course_code'] for s in student_data))
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Absentee List</title>
    <style>
        @page {{
            size: A4 landscape;
            margin: 15mm;
        }}
        body {{
            font-family: 'Times New Roman', serif;
            margin: 0;
            padding: 20px;
            font-size: 11pt;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 3px solid #333;
            padding-bottom: 10px;
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
        .info-section {{
            margin: 20px 0;
            font-size: 11pt;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid black;
            padding: 6px;
            text-align: left;
        }}
        th {{
            background-color: #e5e5e5;
            font-weight: bold;
            font-size: 10pt;
        }}
        td {{
            font-size: 10pt;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #999;
            font-size: 10pt;
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
        <p style="font-size: 10pt; margin-top: 10px;">Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}</p>
    </div>
    
    <div class="info-section">
        <strong>Total Absentees:</strong> {len(student_data)} across {unique_courses} course(s)
    </div>
    
    <table>
        <thead>
            <tr>
                <th style="width: 40px;">S.No</th>
                <th style="width: 110px;">Roll Number</th>
                <th style="width: 200px;">Student Name</th>
                <th style="width: 100px;">Course Code</th>
                <th style="width: 220px;">Course Name</th>
                <th style="width: 95px;">Exam Date</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for idx, student in enumerate(student_data, 1):
        html += f"""            <tr>
                <td>{idx}</td>
                <td>{student['roll_no']}</td>
                <td>{student['name']}</td>
                <td>{student['course_code']}</td>
                <td>{student['course_title']}</td>
                <td>{student['exam_date']}</td>
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
