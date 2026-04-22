"""
SIMPLE ATTENDANCE SHEET GENERATION - REBUILT FROM SCRATCH
Clean, working implementation

This module generates attendance sheets for exam courses.
It fetches student data from Supabase database and creates HTML attendance sheets.
"""

# Import required libraries
from database import repository
from helpers.utils import extract_semester_from_roll_no  # Helper to get semester number from roll number
from io import BytesIO  # For creating in-memory binary streams (used for ZIP files)
import zipfile  # For creating ZIP archives
from datetime import datetime  # For date formatting


def generate_attendance_sheet(course_code, exam_date, semester_id, **kwargs):
    """
    Main function to generate an attendance sheet for a specific course
    
    Parameters:
    - course_code: The course code (e.g., "ME101", "CS201")
    - exam_date: The date of the exam (will be formatted to dd-mm-yyyy)
    - semester_id: The ID of the semester in the database
    - **kwargs: Additional optional parameters (not used currently)
    
    Returns:
    - A tuple: (html_content, message)
      - html_content: The generated HTML string (or None if error)
      - message: Success or error message
    
    How it works:
    1. Fetches semester information from database
    2. Fetches all students registered for this course
    3. Sorts students by Batch → Semester → Name
    4. Generates HTML attendance sheet
    """
    try:
        # STEP 1: Get semester information from database
        # We query the 'semesters' table to get details like academic year, exam type, etc.
        semester = repository.get_semester_by_id(semester_id)
        if not semester:
            return None, "Semester not found"
        
        # STEP 2: Get all students enrolled in this course
        # We query the 'students' table filtering by semester_id and course_code,
        # then apply optional section/instructor/roll filters.
        students = repository.get_students_by_course(
            semester_id,
            course_code,
            {
                'section': kwargs.get('section'),
                'instructor': kwargs.get('instructor'),
                'roll_numbers': kwargs.get('roll_numbers'),
            },
        )

        if not students:
            return None, "No students found for selected filters"
        
        # STEP 3: Sort students in the correct order
        # Sorting order: Batch → Semester (extracted from roll number) → Name (alphabetically)
        def sort_key(s):
            # Get batch (e.g., "B.Tech", "M.Tech"), if missing use "ZZZ" to put at end
            batch = (s.get('timetable_batch') or 'ZZZ').upper()
            # Extract semester number from roll number (e.g., "B210001ME" → 2nd year)
            semester = extract_semester_from_roll_no(s.get('roll_no', ''))
            # Get student name in uppercase for alphabetical sorting
            name = (s.get('name') or '').upper()
            # Return tuple for sorting (Python sorts tuples element by element)
            return (batch, semester, name)
        
        students.sort(key=sort_key)  # Sort the students list using our custom key
        
        # STEP 4: Get course details from first student record
        course_title = students[0].get('course_title', 'Unknown Course')
        instructor = students[0].get('main_instructor', 'Unknown Instructor')
        
        # STEP 5: Check if course has multiple instructors/sections
        # Collect unique instructor-section combinations
        unique_instructors = set()
        unique_sections = set()
        for student in students:
            unique_instructors.add(student.get('main_instructor', 'Unknown'))
            section = student.get('timetable_batch', '')
            if section:
                unique_sections.add(section)
        
        # Create instructor display
        instructor_display = instructor
        
        # If there's only one section, show it beside instructor name
        if len(unique_sections) == 1:
            section = list(unique_sections)[0]
            instructor_display = f"{instructor} (Section: {section})"
        elif len(unique_sections) > 1:
            # Multiple sections - show that in the display
            sections_str = ', '.join(sorted(unique_sections))
            instructor_display = f"{instructor} (Sections: {sections_str})"
        
        # STEP 6: Generate the HTML content
        html = generate_html(course_code, course_title, instructor_display, exam_date, semester, students)
        
        return html, "Success"
        
    except Exception as e:
        # If any error occurs, return None and the error message
        return None, f"Error: {str(e)}"


def generate_html(course_code, course_title, instructor, exam_date, semester, students):
    """
    Generate the actual HTML content for the attendance sheet
    
    Parameters:
    - course_code: Course code (e.g., "ME101")
    - course_title: Full course name (e.g., "Engineering Mechanics")
    - instructor: Name of the course instructor
    - exam_date: Date of exam (will be formatted to dd-mm-yyyy)
    - semester: Dictionary containing semester details (academic_year, semester_type, exam_type)
    - students: List of student dictionaries (already sorted)
    
    Returns:
    - HTML string containing the complete attendance sheet
    
    The HTML includes:
    - Header with institute and department name
    - Exam details (date, course, instructor)
    - Student table with columns for roll no, name, batch, signature, etc.
    - Answer books tracking table
    - Invigilator signature section
    """
    
    # STEP 1: Convert semester type to readable format
    # Database stores 'monsoon' or 'winter', we convert to 'Monsoon' or 'Winter'
    sem_type = {'monsoon': 'Monsoon', 'winter': 'Winter'}.get(
        semester.get('semester_type', ''), 
        semester.get('semester_type', '')
    )
    
    # STEP 2: Convert exam type to full name
    # Database stores 'midsem' or 'endsem', we convert to full examination names
    exam_type = {'midsem': 'Mid Semester Examination', 'endsem': 'End Semester Examination'}.get(
        semester.get('exam_type', ''), 
        semester.get('exam_type', '')
    )
    
    # STEP 3: Format the exam date to dd-mm-yyyy format
    # Input might be 'yyyy-mm-dd' or other formats, we convert to dd-mm-yyyy
    try:
        # Try to parse the date if it's in yyyy-mm-dd format
        if '-' in exam_date and len(exam_date) == 10:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d-%m-%Y')  # Convert to dd-mm-yyyy
        else:
            # If already in correct format or different format, use as-is
            formatted_date = exam_date
    except:
        # If any error in date parsing, use the original date
        formatted_date = exam_date
    
    # STEP 4: Build the HTML structure
    # We create a complete HTML document with inline CSS for printing
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Attendance - {course_code}</title>
    <style>
        /* Basic styling for the attendance sheet */
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 10px; }}
        .header div {{ margin: 3px 0; }}
        .bold {{ font-weight: bold; }}
        /* Table styling - borders and spacing */
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid black; padding: 5px; font-size: 11px; }}
        th {{ background-color: #f0f0f0; }}
        /* Print optimization - reduce margins when printing */
        @media print {{ body {{ margin: 10mm; }} }}
    </style>
</head>
<body>
    <!-- HEADER SECTION: Institute and department name -->
    <div class="header">
        <div class="bold" style="font-size: 14px;">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
        <div class="bold" style="font-size: 12px;">DEPARTMENT OF MECHANICAL ENGINEERING</div>
        <div class="bold" style="font-size: 12px;">Statement of Answer Books and Bio breaks Details</div>
    </div>

    <!-- EXAM DETAILS SECTION: Shows exam info, date, course details -->
    <div style="font-size: 11px; margin: 10px 0;">
        <div><strong>Examination:</strong> {exam_type}</div>
        <div>
            <strong>Semester:</strong> {sem_type} &nbsp;&nbsp;
            <strong>Academic Year:</strong> {semester.get('academic_year', '')} &nbsp;&nbsp;
            <strong>Date:</strong> {formatted_date}
        </div>
        <div>
            <strong>Course Code:</strong> {course_code} &nbsp;&nbsp;
            <strong>Course Name:</strong> {course_title} &nbsp;&nbsp;
            <strong>Instructor:</strong> {instructor}
        </div>
    </div>

    <!-- STUDENT ATTENDANCE TABLE: Main table with student details -->
    <table>
        <thead>
            <tr>
                <th style="width: 5%;">Sl. No.</th>
                <th style="width: 12%;">Roll No.</th>
                <th style="width: 8%;">Batch</th>
                <th style="width: 30%;">Student Name</th>
                <th style="width: 15%;">Additional Sheets</th>
                <th style="width: 15%;">Bio Break</th>
                <th style="width: 15%;">Signature</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # STEP 5: Add a row for each student
    # Loop through sorted students and create table rows
    for i, student in enumerate(students, 1):  # enumerate(students, 1) gives us index starting from 1
        roll = student.get('roll_no', '')  # Get roll number, empty string if not found
        name = student.get('name', '')  # Get student name
        batch = student.get('timetable_batch', '') or '-'  # Get batch, show '-' if empty
        
        # Add HTML row for this student (columns left blank for manual filling during exam)
        html += f"""
            <tr>
                <td>{i}</td>
                <td>{roll}</td>
                <td>{batch}</td>
                <td>{name}</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>"""
    
    html += """
        </tbody>
    </table>

    <div style="margin-top: 20px;">
        <table>
            <tr>
                <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Answer Books</th>
                <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Invigilators</th>
            </tr>
            <tr>
                <td style="width: 12%;"></td>
                <th style="width: 8%;">Main</th>
                <th style="width: 13%;">Additional</th>
                <th style="width: 10%;">Sl. No.</th>
                <th style="width: 35%;">Name</th>
                <th style="width: 22%;">Signature</th>
            </tr>
            <tr>
                <td><strong>Received</strong></td>
                <td></td>
                <td></td>
                <td>1</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td><strong>Used</strong></td>
                <td></td>
                <td></td>
                <td>2</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td><strong>Balance</strong></td>
                <td></td>
                <td></td>
                <td>3</td>
                <td></td>
                <td></td>
            </tr>
        </table>
    </div>

</body>
</html>
"""
    
    return html


def generate_all_attendance_sheets_zip(semester_id, exam_date, **kwargs):
    """Generate ZIP file with all attendance sheets for a semester"""
    try:
        # Get all courses for this semester
        courses = repository.get_courses_for_semester(semester_id)

        if not courses:
            return None, "No courses found"
        
        # Create ZIP in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            count = 0
            for course_code, _ in courses:
                html_content, message = generate_attendance_sheet(course_code, exam_date, semester_id)
                
                if html_content:
                    filename = f"Attendance_{course_code}_{exam_date}.html"
                    zipf.writestr(filename, html_content.encode('utf-8'))
                    count += 1
            
            if count == 0:
                return None, "No attendance sheets generated"
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f"Generated {count} attendance sheets"
        
    except Exception as e:
        return None, f"Error: {str(e)}"
