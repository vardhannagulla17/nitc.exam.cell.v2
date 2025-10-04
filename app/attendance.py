import os
import shutil
import tempfile
import zipfile
import sqlite3
from helpers.utils import sort_by_roll_number
from flask import current_app

# Get download folder path

def generate_attendance_sheet(course_code, exam_date, semester_id, preview=False):
    """Generate HTML attendance sheet for a specific course and date using NITC format"""
    download_folder = current_app.config['DOWNLOAD_FOLDER']
    os.makedirs(download_folder, exist_ok=True)  # Ensure download folder exists
    try:
        # Get semester information
        import sqlite3
        db_path = os.path.join(current_app.config['BASE_DIR'], 'exam_cell.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT academic_year, semester_type, degree_level, exam_type, db_name FROM semesters WHERE id = ?', (semester_id,))
        semester_info = cursor.fetchone()
        conn.close()
        
        if not semester_info:
            return None, "Semester not found"
        
        academic_year, semester_type, degree_level, exam_type, db_name = semester_info
        
        # Get students from semester-specific database
        students_sorted = get_sorted_students(db_name, course_code)
        if not students_sorted:
            return None, "No students found for this course"
        
        # Get course details
        course_title = students_sorted[0][2] if students_sorted else "Unknown Course"
        instructor_name = students_sorted[0][3] if students_sorted else "Unknown Instructor"
        
        # Generate HTML content
        html_content = generate_html_content(
            course_code, exam_date, academic_year, semester_type, 
            degree_level, exam_type, course_title, instructor_name, 
            students_sorted
        )
        
        if preview:
            return html_content, "Preview generated successfully"
        
        # Save HTML file
        filename = f"Attendance_{academic_year}_{semester_type}_{degree_level}_{exam_type}_{course_code}_{exam_date}.html"
        filepath = os.path.join(current_app.config['DOWNLOAD_FOLDER'], filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath, "Attendance sheet generated successfully"
        
    except Exception as e:
        return None, f"Error generating attendance sheet: {str(e)}"

# NOTE: simple attendance sheet generator removed. The detailed attendance
# sheet (generate_attendance_sheet / generate_html_content) now includes
# signature, bio-break and additional sheets columns and should be used
# for both preview and download.

def generate_all_attendance_sheets_zip(semester_id, exam_date):
    """Generate all attendance sheets for a semester and create a ZIP file with program and course folders"""
    try:
        # Get base directory and ensure download folder exists
        base_dir = current_app.config['BASE_DIR']
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        os.makedirs(download_folder, exist_ok=True)
        
        # Connect to database using absolute path
        db_path = os.path.join(base_dir, 'exam_cell.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT academic_year, semester_type, degree_level, exam_type, db_name FROM semesters WHERE id = ?', (semester_id,))
        semester_info = cursor.fetchone()
        conn.close()
        
        if not semester_info:
            return None, "Semester not found"
        
        academic_year, semester_type, degree_level, exam_type, db_name = semester_info
        
        # Get all courses from semester-specific database
        courses = get_courses(db_name)
        if not courses:
            return None, "No courses found for this semester"
        
        # Create temporary directory for organizing files
        temp_dir = tempfile.mkdtemp()
        generated_files = []
        
        # Create program level directories
        program_dirs = {'UG': 'Undergraduate', 'PG': 'Postgraduate', 'PhD': 'PhD'}
        
        # Ensure the download folder exists
        download_folder = current_app.config['DOWNLOAD_FOLDER']
        os.makedirs(download_folder, exist_ok=True)
        
        # Create program level directories in both temp and download folders
        for program in program_dirs.keys():
            os.makedirs(os.path.join(temp_dir, program), exist_ok=True)
            os.makedirs(os.path.join(download_folder, program), exist_ok=True)
        
        # Create course folders and generate files
        for course_code, course_title in courses:
            # Determine program level based on students' roll number prefixes (B=UG, M=PG, P=PhD)
            try:
                students_for_course = get_sorted_students(db_name, course_code) or []
                roll_prefixes = [str(s[0]).strip().upper()[:1] for s in students_for_course if s and s[0]]
                has_ug = any(p == 'B' for p in roll_prefixes)
                has_pg = any(p == 'M' for p in roll_prefixes)
                has_phd = any(p == 'P' for p in roll_prefixes)
                if has_pg and not has_ug and not has_phd:
                    program_level = 'PG'
                elif has_ug and not has_pg and not has_phd:
                    program_level = 'UG'
                elif has_phd and not has_ug and not has_pg:
                    program_level = 'PhD'
                else:
                    # Mixed or unknown: prefer UG if present, else PG, else default UG
                    program_level = 'UG' if has_ug else ('PG' if has_pg else ('PhD' if has_phd else 'UG'))
            except Exception:
                # Fallback to previous heuristic based on course code
                program_level = 'PG' if course_code.startswith('M') else 'PhD' if course_code.startswith('P') else 'UG'
            
            # Create course directory with absolute paths
            temp_program_dir = os.path.join(temp_dir, program_level)
            course_dir = os.path.join(temp_program_dir, course_code)
            
            # Ensure both program and course directories exist
            os.makedirs(temp_program_dir, exist_ok=True)
            os.makedirs(course_dir, exist_ok=True)
            
            # Generate detailed attendance sheet (with bio breaks)
            filepath, message = generate_attendance_sheet(course_code, exam_date, semester_id, preview=False)
            if filepath:
                filename = f"Detailed_{os.path.basename(filepath)}"
                dest_path = os.path.join(course_dir, filename)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                try:
                    shutil.copy2(filepath, dest_path)
                except Exception as e:
                    print(f"Warning: Could not copy file {filepath} to {dest_path}: {str(e)}")
                    continue
                generated_files.append((dest_path, os.path.join(program_level, course_code, filename)))
            
            # Note: simplified attendance sheet is no longer generated separately.
            # The detailed attendance sheet now includes signature and bio-break/additional sheets columns.
        
        if not generated_files:
            return None, "No attendance sheets could be generated"
        
        # Create ZIP file with organized structure
        zip_filename = f"AttendanceSheets_{academic_year}_{semester_type}_{degree_level}_{exam_type}_{exam_date}.zip"
        zip_filepath = os.path.join(current_app.config['DOWNLOAD_FOLDER'], zip_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(zip_filepath), exist_ok=True)
        
        # Remove existing ZIP file if it exists
        if os.path.exists(zip_filepath):
            try:
                os.remove(zip_filepath)
            except Exception as e:
                print(f"Warning: Could not remove existing ZIP file: {str(e)}")
        
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add a README file explaining the structure
            readme_content = f"""Attendance Sheets Organization
----------------------------
Academic Year: {academic_year}
Semester: {semester_type}
Examination: {'Mid Semester' if exam_type == 'midsem' else 'End Semester' if exam_type == 'endsem' else exam_type} Examination
Date: {exam_date}

Folder Structure:
---------------
/UG/ - Undergraduate Courses
/PG/ - Postgraduate Courses
/PhD/ - PhD Courses

Each course folder contains:
1. Detailed_*.html - Full attendance sheet with bio-breaks tracking
2. Simple_*.html - Basic attendance sheet with only signature column
"""
            zipf.writestr('README.txt', readme_content)
            
            # Add all generated files preserving folder structure
            for file_path, rel_path in generated_files:
                zipf.write(file_path, rel_path)
        
        # Get the count before cleanup
        total_files = len(generated_files)
        
        # Cleanup temp directory and generated files
        try:
            # Close any open file handles
            for file_path, _ in generated_files:
                try:
                    if os.path.exists(file_path):
                        os.chmod(file_path, 0o777)  # Ensure we have permissions to remove
                except Exception:
                    pass  # Ignore permission setting errors
            
            # Remove the temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temporary directory: {str(cleanup_error)}")
            # Continue execution as this is not a critical error
        
        return zip_filepath, f"Generated {total_files} attendance sheets in ZIP file"
        
    except Exception as e:
        return None, f"Error generating bulk attendance sheets: {str(e)}"

# Helper functions
def get_sorted_students(db_name, course_code):
    """Get sorted list of students for a course"""
    import sqlite3
    try:
        # Ensure db_name is an absolute path
        if not os.path.isabs(db_name):
            db_name = os.path.join(current_app.config['BASE_DIR'], db_name)
        sem_conn = sqlite3.connect(db_name)
        cursor = sem_conn.cursor()
        cursor.execute('''
            SELECT roll_no, name, course_title, main_instructor, program_name 
            FROM students 
            WHERE course_code = ? 
            ORDER BY roll_no
        ''', (course_code,))
        students = cursor.fetchall()
        sem_conn.close()
        return sort_by_roll_number(students)
    except sqlite3.Error:
        return []

def get_courses(db_name):
    """Get all courses from a semester database"""
    import sqlite3
    try:
        if not os.path.isabs(db_name):
            db_name = os.path.join(current_app.config['BASE_DIR'], db_name)
        sem_conn = sqlite3.connect(db_name)
        cursor = sem_conn.cursor()
        cursor.execute('SELECT DISTINCT course_code, course_title FROM students ORDER BY course_code')
        courses = cursor.fetchall()
        sem_conn.close()
        return courses
    except sqlite3.Error:
        return []

# HTML generation functions
def generate_html_content(course_code, exam_date, academic_year, semester_type, degree_level, exam_type, course_title, instructor_name, students_sorted):
    """Generate HTML content for attendance sheet"""
    # Calculate pagination
    rows_per_page = 60
    total_students = len(students_sorted)
    total_pages = max(1, (total_students + rows_per_page - 1) // rows_per_page)
    
    # Display mappings
    exam_type_display = {
        'midsem': 'Mid Semester Examination',
        'endsem': 'End Semester Examination'
    }
    
    semester_display = {
        'monsoon': 'Monsoon',
        'winter': 'Winter'
    }
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Attendance Sheet - {course_title} - {instructor_name}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 10px; 
        }}
        .institute-name {{ 
            font-weight: bold; 
            font-size: 14px; 
        }}
        .department {{ 
            font-weight: bold; 
            font-size: 12px; 
            margin-top: 3px; 
        }}
        .form-title {{ 
            font-weight: bold; 
            font-size: 12px; 
            margin-top: 6px; 
        }}
        .page-no {{ 
            font-size: 10px; 
            margin-top: 4px; 
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 8px 0; 
        }}
        th, td {{ 
            border: 1px solid black; 
            padding: 4px; 
            text-align: left; 
            font-size: 10px; 
        }}
        th {{ 
            background-color: #f0f0f0; 
            font-weight: bold; 
        }}
        @media print {{
            body {{ 
                margin: 10mm; 
            }}
            .page {{ 
                page-break-after: always; 
            }}
            .page:last-child {{ 
                page-break-after: auto; 
            }}
        }}
    </style>
</head>
<body>
"""
    
    # Generate pages
    for page_num in range(total_pages):
        start_idx = page_num * rows_per_page
        end_idx = min(start_idx + rows_per_page, total_students)
        page_students = students_sorted[start_idx:end_idx]
        
        html_content += f"""
    <div class="page">
        <!-- Header Section -->
        <div class="header">
            <div class="institute-name">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
            <div class="department">DEPARTMENT OF MECHANICAL ENGINEERING</div>
            <div class="form-title">Statement of Answer Books and Bio breaks Details</div>
            <div class="page-no">Page {page_num + 1} of {total_pages}</div>
        </div>

        <!-- Course Information Section -->
        <div class="info-section">
            <div><strong>Name of the Examination:</strong> {exam_type_display.get(exam_type, exam_type)}</div>
            <div>
                <strong>Semester:</strong> {semester_display.get(semester_type, semester_type)} &nbsp;&nbsp;
                <strong>Academic Year:</strong> {academic_year} &nbsp;&nbsp;
                <strong>Date:</strong> {exam_date} &nbsp;&nbsp;
                <strong>Time:</strong> ____________
            </div>
            <div>
                <strong>Course Code:</strong> {course_code} &nbsp;&nbsp;
                <strong>Course Name:</strong> {course_title} &nbsp;&nbsp;
                <strong>Instructor:</strong> {instructor_name}
            </div>
        </div>

        <!-- Students Table -->
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">Sl. No.</th>
                    <th style="width: 12%;">Roll No.</th>
                    <th style="width: 40%;">Student Name</th>
                    <th style="width: 12%;">No. of Additional Sheets</th>
                    <th style="width: 16%;">Details of Bio Break</th>
                    <th style="width: 15%;">Signature</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add student rows for this page
        for i in range(rows_per_page):
            serial_no = start_idx + i + 1
            if i < len(page_students):
                student = page_students[i]
                html_content += f"""
                <tr>
                    <td>{serial_no}</td>
                    <td>{student[0] if student[0] else ''}</td>
                    <td>{student[1] if student[1] else ''}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>"""
            else:
                # Empty rows to fill the page
                html_content += f"""
                <tr>
                    <td>{serial_no}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>"""
        
        html_content += """
            </tbody>
        </table>

        <!-- Invigilator Signature Section -->
        <div style="margin-top: 20px;">
            <strong>Signature of invigilators with Date</strong>
            <table style="margin-top: 10px;">
                <tr>
                    <th style="width: 10%;">Sl. No.</th>
                    <th style="width: 40%;">Name</th>
                    <th style="width: 25%;">Date</th>
                    <th style="width: 25%;">Signature</th>
                </tr>
                <tr><td>1</td><td></td><td></td><td></td></tr>
                <tr><td>2</td><td></td><td></td><td></td></tr>
            </table>
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    return html_content

# simple sheet removed