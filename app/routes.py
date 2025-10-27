from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from werkzeug.utils import secure_filename
import os
from .models import (
    load_excel_to_db, get_user_by_credentials,
    get_all_semesters, get_courses_for_semester,
    get_semesters_for_program_level
)
from .attendance import (
    generate_attendance_sheet,
    generate_all_attendance_sheets_zip
)
from helpers.file_utils import allowed_file, get_uploaded_files, delete_file_safely
from helpers.database_utils import get_semester_stats, cleanup_semester_databases

bp = Blueprint('main', __name__)

# DateTime filter will be added to the app instance in __init__.py

# Routes
@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!', 'info')
    return redirect(url_for('main.login'))

@bp.route('/delete_file/<filename>')
def delete_file(filename):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Only administrators can delete files.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if delete_file_safely(filepath):
            flash(f'File {filename} has been deleted successfully.', 'success')
            # Also clear semester data and remove semester databases
            cleanup_semester_databases()
        else:
            flash(f'File {filename} not found.', 'error')
    except Exception as e:
        flash(f'Error deleting file {filename}: {str(e)}', 'error')
    
    return redirect(url_for('main.dashboard'))

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    stats = get_semester_stats()
    uploaded_files = get_uploaded_files() if session.get('role') == 'admin' else []
    
    return render_template('dashboard.html',
                         username=session['username'],
                         role=session['role'],
                         total_students=stats['total_students'],
                         total_courses=stats['total_courses'],
                         total_semesters=stats['total_semesters'],
                         uploaded_files=uploaded_files)

@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # Only admin users can access upload functionality
    if session.get('role') != 'admin':
        flash('Access denied. Only administrators can upload files.', 'error')
        return redirect(url_for('main.dashboard'))
    
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            success, message = load_excel_to_db(filepath, academic_year, semester_type, sheet_type, exam_type)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid file type! Please upload Excel files only.', 'error')
    
    return render_template('upload.html')

@bp.route('/download', methods=['GET', 'POST'])
def download_attendance():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # Initialize variables
    courses = []
    selected_semester = None
    selected_program = None
    program_levels = current_app.config.get('PROGRAM_LEVELS', ['UG', 'PG', 'PhD'])
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
                filepath, message = generate_all_attendance_sheets_zip(semester_id, exam_date)
                if filepath:
                    flash(message, 'success')
                    return send_file(filepath, as_attachment=True)
                flash(message, 'error')
                    
            elif action in ['preview'] and course_code:
                print(f"DEBUG: Generating preview for {course_code}")
                if action == 'preview':
                    html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True)
                else:
                    html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True)
                    
                if html_content:
                    return html_content
                flash(message, 'error')
                    
            elif action in ['download'] and course_code:
                print(f"DEBUG: Generating download for {course_code}")
                if action == 'download':
                    filepath, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=False)
                else:
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
