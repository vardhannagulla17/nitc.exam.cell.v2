from flask import render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
from app.config import app, allowed_file
from app.models import (
    init_db, load_excel_to_db, get_user_by_credentials,
    get_semester_stats, get_all_semesters, get_courses_for_semester
)
from app.attendance import (
    generate_attendance_sheet, generate_simple_attendance_sheet,
    generate_all_attendance_sheets_zip
)

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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    stats = get_semester_stats()
    return render_template('dashboard.html',
                         username=session['username'],
                         total_students=stats['total_students'],
                         total_courses=stats['total_courses'],
                         total_semesters=stats['total_semesters'])

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        academic_year = request.form.get('academic_year')
        semester_type = request.form.get('semester_type')
        degree_level = request.form.get('degree_level')
        exam_type = request.form.get('exam_type')
        
        # Validate form data
        if not all([academic_year, semester_type, degree_level, exam_type]):
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            success, message = load_excel_to_db(filepath, academic_year, semester_type, degree_level, exam_type)
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
    
    semesters = get_all_semesters()
    courses = []
    selected_semester = None
    
    if request.method == 'POST':
        action = request.form.get('action', 'download')
        semester_id = request.form.get('semester_id')
        course_code = request.form.get('course_code')
        exam_date = request.form.get('exam_date')
        
        if not semester_id or not exam_date:
            flash('Please select semester and exam date!', 'error')
            return render_template('download.html', semesters=semesters, courses=courses)
        
        courses = get_courses_for_semester(semester_id)
        selected_semester = semester_id
        
        if action == 'download_all':
            filepath, message = generate_all_attendance_sheets_zip(semester_id, exam_date)
            if filepath:
                flash(message, 'success')
                return send_file(filepath, as_attachment=True)
            else:
                flash(message, 'error')
                
        elif action == 'preview' and course_code:
            html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=True)
            if html_content:
                return html_content
            else:
                flash(message, 'error')
                
        elif action == 'preview_simple' and course_code:
            html_content, message = generate_simple_attendance_sheet(course_code, exam_date, semester_id, preview=True)
            if html_content:
                return html_content
            else:
                flash(message, 'error')
                
        elif action == 'download' and course_code:
            filepath, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=False)
            if filepath:
                flash(message, 'success')
                return send_file(filepath, as_attachment=True)
            else:
                flash(message, 'error')
                
        elif action == 'download_simple' and course_code:
            filepath, message = generate_simple_attendance_sheet(course_code, exam_date, semester_id, preview=False)
            if filepath:
                flash(message, 'success')
                return send_file(filepath, as_attachment=True)
            else:
                flash(message, 'error')
        else:
            flash('Please select a course!', 'error')
    
    if request.args.get('semester_id'):
        semester_id = request.args.get('semester_id')
        courses = get_courses_for_semester(semester_id)
        selected_semester = semester_id
    
    return render_template('download.html',
                         semesters=semesters,
                         courses=courses,
                         selected_semester=selected_semester)