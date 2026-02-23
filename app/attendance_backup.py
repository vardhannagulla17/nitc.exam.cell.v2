"""
Attendance Sheet Generation Module - Rebuilt from Scratch
Generates HTML attendance sheets for courses with proper sorting and filtering
"""
import os
import zipfile
from io import BytesIO
from flask import current_app
from supabase_client import supabase
from app.database import USE_SUPABASE_DB
from helpers.utils import extract_semester_from_roll_no


def generate_attendance_sheet(course_code, exam_date, semester_id, preview=False, 
                              in_memory=False, program_level=None, section=None, 
                              instructor=None, roll_numbers=None):
    """
    Generate HTML attendance sheet for a course
    
    Args:
        course_code: Course code (e.g., 'ME3411E')
        exam_date: Exam date (YYYY-MM-DD)
        semester_id: Semester ID from database
        preview: If True, returns HTML directly
        in_memory: If True, returns HTML (for ZIP generation)
        program_level: Filter by UG/PG/PhD
        section: Filter by timetable_batch
        instructor: Filter by main_instructor
        roll_numbers: List of specific roll numbers (for absentee sheets)
    
    Returns:
        (html_content, message) tuple
    """
    try:
        print(f"\n{'='*60}")
        print(f"[ATTENDANCE] START: course={course_code}, date={exam_date}, semester={semester_id}")
        print(f"[ATTENDANCE] Filters: program={program_level}, section={section}, instructor={instructor}")
        print(f"{'='*60}")
        
        # Validate inputs
        if not course_code:
            print("[ATTENDANCE] ERROR: Missing course_code")
            return None, "Course code is required"
        if not semester_id:
            print("[ATTENDANCE] ERROR: Missing semester_id")
            return None, "Semester ID is required"
        if not exam_date:
            print("[ATTENDANCE] ERROR: Missing exam_date")
            return None, "Exam date is required"
        
        # Get semester information
        print("[ATTENDANCE] Step 1: Getting semester info...")
        semester_info = _get_semester_info(semester_id)
        if not semester_info:
            print(f"[ATTENDANCE] ERROR: Semester {semester_id} not found in database")
            return None, f"Semester {semester_id} not found"
        print(f"[ATTENDANCE] Semester info: {semester_info}")
        
        # Get students for the course with filters applied
        print(f"[ATTENDANCE] Step 2: Getting students for course {course_code}...")
        students = _get_students_for_course(
            semester_id, course_code, program_level, 
            section, instructor, roll_numbers
        )
        
        print(f"[ATTENDANCE] Found {len(students) if students else 0} students")
        
        if not students:
            filter_msg = []
            if section and section != 'all': filter_msg.append(f"section {section}")
            if instructor: filter_msg.append(f"instructor {instructor}")
            if roll_numbers: filter_msg.append("absentees only")
            
            msg = f"No students found for course {course_code}"
            if filter_msg:
                msg += f" with filters: {', '.join(filter_msg)}"
            print(f"[ATTENDANCE] ERROR: {msg}")
            return None, msg
        
        # Sort students: Batch → Semester → Alphabetical
        print("[ATTENDANCE] Step 3: Sorting students...")
        students_sorted = _sort_students_by_batch_semester_name(students)
        print(f"[ATTENDANCE] Sorted {len(students_sorted)} students")
        
        # Extract course metadata
        course_title = students_sorted[0].get('course_title', 'Unknown Course')
        instructor_name = students_sorted[0].get('main_instructor', 'Unknown Instructor')
        print(f"[ATTENDANCE] Course: {course_title}, Instructor: {instructor_name}")
        
        # Generate HTML content
        print("[ATTENDANCE] Step 4: Generating HTML...")
        html_content = _generate_html(
            course_code=course_code,
            exam_date=exam_date,
            semester_info=semester_info,
            course_title=course_title,
            instructor_name=instructor_name,
            students=students_sorted
        )
        
        print(f"[ATTENDANCE] SUCCESS: Generated {len(html_content)} chars of HTML")
        print(f"{'='*60}\n")
        return html_content, "Generated successfully"
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[ATTENDANCE] EXCEPTION: {type(e).__name__}: {str(e)}")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return None, f"Error: {str(e)}"


def generate_all_attendance_sheets_zip(semester_id, exam_date, in_memory=True, program_level=None):
    """
    Generate attendance sheets for all courses and return as ZIP file
    
    Args:
        semester_id: Semester ID
        exam_date: Exam date (YYYY-MM-DD)
        in_memory: Always True for Vercel compatibility
        program_level: Filter by UG/PG/PhD
    
    Returns:
        (zip_bytes, message) tuple
    """
    try:
        # Get semester information
        semester_info = _get_semester_info(semester_id)
        if not semester_info:
            return None, "Semester not found"
        
        # Get all courses
        courses = _get_all_courses(semester_id, program_level)
        if not courses:
            return None, "No courses found for this semester"
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add README
            readme = _generate_readme(semester_info, exam_date, len(courses))
            zipf.writestr('README.txt', readme)
            
            # Generate attendance sheet for each course
            files_added = 0
            for course_code, course_title in courses:
                # Determine program level from course
                prog_level = _detect_program_level(semester_id, course_code)
                
                # Generate HTML
                html_content, message = generate_attendance_sheet(
                    course_code=course_code,
                    exam_date=exam_date,
                    semester_id=semester_id,
                    preview=True,
                    in_memory=True,
                    program_level=program_level
                )
                
                if html_content:
                    # Create path: ProgramLevel/CourseCode/filename.html
                    filename = f"Attendance_{course_code}_{exam_date}.html"
                    path = f"{prog_level}/{course_code}/{filename}"
                    zipf.writestr(path, html_content.encode('utf-8'))
                    files_added += 1
            
            if files_added == 0:
                return None, "No attendance sheets could be generated"
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f"Generated {files_added} attendance sheets"
    
    except Exception as e:
        print(f"[ERROR] generate_all_attendance_sheets_zip: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, f"Error: {str(e)}"


# ==================== PRIVATE HELPER FUNCTIONS ====================

def _get_semester_info(semester_id):
    """Get semester information from database"""
    try:
        if USE_SUPABASE_DB and supabase:
            result = supabase.table('semesters')\
                .select('academic_year, semester_type, degree_level, exam_type')\
                .eq('id', semester_id)\
                .execute()
            
            if result.data:
                return result.data[0]
        return None
    except Exception as e:
        print(f"[ERROR] _get_semester_info: {str(e)}")
        return None


def _get_students_for_course(semester_id, course_code, program_level=None, 
                             section=None, instructor=None, roll_numbers=None):
    """
    Get students for a course with filters
    
    Returns:
        List of dicts with keys: roll_no, name, course_title, main_instructor, timetable_batch
    """
    try:
        print(f"[GET_STUDENTS] semester_id={semester_id}, course={course_code}, filters=program:{program_level}, section:{section}, instructor:{instructor}")
        
        if not (USE_SUPABASE_DB and supabase):
            print("[GET_STUDENTS] ERROR: Supabase not configured")
            return []
        
        # Build query with pagination support
        all_students = []
        page_size = 1000
        offset = 0
        
        print(f"[GET_STUDENTS] Starting paginated query...")
        while True:
            query = supabase.table('students')\
                .select('roll_no, name, course_title, main_instructor, timetable_batch')\
                .eq('semester_id', semester_id)\
                .eq('course_code', course_code)
            
            # Apply filters
            if program_level:
                prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
                prefix = prefix_map.get(program_level)
                if prefix:
                    query = query.like('roll_no', f'{prefix}%')
                    print(f"[GET_STUDENTS] Applied program_level filter: {prefix}%")
            
            if section and section != 'all':
                query = query.eq('timetable_batch', section)
                print(f"[GET_STUDENTS] Applied section filter: {section}")
            
            if instructor:
                query = query.eq('main_instructor', instructor)
                print(f"[GET_STUDENTS] Applied instructor filter: {instructor}")
            
            if roll_numbers:
                query = query.in_('roll_no', roll_numbers)
                print(f"[GET_STUDENTS] Applied roll_numbers filter: {len(roll_numbers)} students")
            
            # Execute query with pagination
            print(f"[GET_STUDENTS] Executing query at offset {offset}...")
            result = query.range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                print(f"[GET_STUDENTS] No more data at offset {offset}")
                break
            
            print(f"[GET_STUDENTS] Got {len(result.data)} students at offset {offset}")
            all_students.extend(result.data)
            
            if len(result.data) < page_size:
                break
            
            offset += page_size
        
        print(f"[GET_STUDENTS] TOTAL: {len(all_students)} students retrieved")
        return all_students
    
    except Exception as e:
        print(f"[GET_STUDENTS] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def _get_all_courses(semester_id, program_level=None):
    """
    Get all unique courses for a semester
    
    Returns:
        List of tuples (course_code, course_title)
    """
    try:
        if not (USE_SUPABASE_DB and supabase):
            return []
        
        # Get all students with pagination
        all_students = []
        page_size = 1000
        offset = 0
        
        while True:
            query = supabase.table('students')\
                .select('course_code, course_title, roll_no')\
                .eq('semester_id', semester_id)
            
            if program_level:
                prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
                prefix = prefix_map.get(program_level)
                if prefix:
                    query = query.like('roll_no', f'{prefix}%')
            
            result = query.range(offset, offset + page_size - 1).execute()
            
            if not result.data:
                break
            
            all_students.extend(result.data)
            
            if len(result.data) < page_size:
                break
            
            offset += page_size
        
        # Extract unique courses
        courses_dict = {}
        for row in all_students:
            code = row['course_code']
            if code not in courses_dict:
                courses_dict[code] = row['course_title']
        
        # Return sorted list
        return sorted([(code, title) for code, title in courses_dict.items()])
    
    except Exception as e:
        print(f"[ERROR] _get_all_courses: {str(e)}")
        return []


def _sort_students_by_batch_semester_name(students):
    """
    Sort students by: BATCH → SEMESTER → ALPHABETICAL
    
    Args:
        students: List of dicts with roll_no, name, timetable_batch
    
    Returns:
        Sorted list
    """
    def sort_key(student):
        # 1. Batch (timetable_batch) - PRIMARY SORT
        batch = student.get('timetable_batch', '') or ''
        batch = batch.strip().upper() if batch else 'ZZZ99'  # Push empty batches to end
        
        # 2. Semester (calculated from roll number) - SECONDARY SORT
        semester = extract_semester_from_roll_no(student.get('roll_no', ''))
        
        # 3. Name (alphabetical) - TERTIARY SORT
        name = student.get('name', '').strip().upper()
        
        return (batch, semester, name)
    
    return sorted(students, key=sort_key)


def _detect_program_level(semester_id, course_code):
    """
    Detect program level (UG/PG/PhD) for a course based on student roll numbers
    """
    try:
        students = _get_students_for_course(semester_id, course_code)
        
        if not students:
            return 'UG'  # Default
        
        # Check first character of roll numbers
        prefixes = [s['roll_no'][0] for s in students if s.get('roll_no')]
        
        has_b = any(p == 'B' for p in prefixes)
        has_m = any(p == 'M' for p in prefixes)
        has_p = any(p == 'P' for p in prefixes)
        
        # Determine dominant program level
        if has_m and not has_b and not has_p:
            return 'PG'
        elif has_p and not has_b and not has_m:
            return 'PhD'
        else:
            return 'UG'  # Default or mixed
    
    except Exception:
        return 'UG'


def _generate_html(course_code, exam_date, semester_info, course_title, instructor_name, students):
    """
    Generate HTML content for attendance sheet
    """
    # Display mappings
    exam_type_map = {
        'midsem': 'Mid Semester Examination',
        'endsem': 'End Semester Examination'
    }
    semester_map = {
        'monsoon': 'Monsoon',
        'winter': 'Winter'
    }
    
    # Extract info
    academic_year = semester_info.get('academic_year', '')
    semester_type = semester_map.get(semester_info.get('semester_type', ''), semester_info.get('semester_type', ''))
    exam_type = exam_type_map.get(semester_info.get('exam_type', ''), semester_info.get('exam_type', ''))
    
    # Pagination
    rows_per_page = 60
    total_students = len(students)
    total_pages = max(1, (total_students + rows_per_page - 1) // rows_per_page)
    
    # Start HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Attendance Sheet - {course_code}</title>
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
        .info-section {{
            font-size: 10px;
            margin: 8px 0;
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
            body {{ margin: 10mm; }}
            .page {{ page-break-after: always; }}
            .page:last-child {{ page-break-after: auto; }}
        }}
    </style>
</head>
<body>
"""
    
    # Generate pages
    for page_num in range(total_pages):
        start_idx = page_num * rows_per_page
        end_idx = min(start_idx + rows_per_page, total_students)
        page_students = students[start_idx:end_idx]
        
        html += f"""
    <div class="page">
        <!-- Header -->
        <div class="header">
            <div class="institute-name">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
            <div class="department">DEPARTMENT OF MECHANICAL ENGINEERING</div>
            <div class="form-title">Statement of Answer Books and Bio breaks Details</div>
            <div class="page-no">Page {page_num + 1} of {total_pages}</div>
        </div>

        <!-- Course Information -->
        <div class="info-section">
            <div><strong>Name of the Examination:</strong> {exam_type}</div>
            <div>
                <strong>Semester:</strong> {semester_type} &nbsp;&nbsp;
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
                    <th style="width: 7%;">Batch</th>
                    <th style="width: 32%;">Student Name</th>
                    <th style="width: 13%;">No. of Additional Sheets</th>
                    <th style="width: 16%;">Details of Bio Break</th>
                    <th style="width: 15%;">Signature</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add student rows
        for i, student in enumerate(page_students):
            serial_no = start_idx + i + 1
            roll_no = student.get('roll_no', '')
            name = student.get('name', '')
            batch = student.get('timetable_batch', '') or '-'
            
            html += f"""
                <tr>
                    <td>{serial_no}</td>
                    <td>{roll_no}</td>
                    <td>{batch}</td>
                    <td>{name}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>"""
        
        html += """
            </tbody>
        </table>

        <!-- Answer Books and Invigilators -->
        <div style="margin-top: 20px;">
            <table>
                <tr>
                    <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of Answer Books</th>
                    <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of Invigilators</th>
                </tr>
                <tr>
                    <td style="width: 12%;"></td>
                    <th style="width: 8%; text-align: center;">Main</th>
                    <th style="width: 13%; text-align: center;">Additional</th>
                    <th style="width: 10%; text-align: center;">Sl. No.</th>
                    <th style="width: 35%; text-align: center;">Name</th>
                    <th style="width: 22%; text-align: center;">Signature</th>
                </tr>
                <tr>
                    <td><strong>Received</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">1</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td><strong>Used</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">2</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td><strong>Balance</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">3</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <th colspan="6" style="background-color: #d3d3d3; text-align: center;">Details of Absentees</th>
                </tr>
                <tr>
                    <th style="text-align: center;">No. of Absentees</th>
                    <td></td>
                    <th colspan="4" style="text-align: center;">Roll no. of Absentees</th>
                </tr>
            </table>
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    return html


def _generate_readme(semester_info, exam_date, course_count):
    """Generate README content for ZIP file"""
    exam_type_map = {
        'midsem': 'Mid Semester',
        'endsem': 'End Semester'
    }
    
    return f"""Attendance Sheets
==================

Academic Year: {semester_info.get('academic_year', 'N/A')}
Semester: {semester_info.get('semester_type', 'N/A').title()}
Examination: {exam_type_map.get(semester_info.get('exam_type', ''), semester_info.get('exam_type', 'N/A'))}
Date: {exam_date}

Total Courses: {course_count}

Folder Structure:
-----------------
/UG/     - Undergraduate Courses
/PG/     - Postgraduate Courses 
/PhD/    - PhD Courses

Each course folder contains:
- Attendance_{CourseCode}_{Date}.html

Sorting:
--------
Students are sorted by:
1. Batch (timetable_batch)
2. Semester (calculated from roll number)
3. Name (alphabetical A-Z)

Generated by NITC Exam Cell Management System
"""
