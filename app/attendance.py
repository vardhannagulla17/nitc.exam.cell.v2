"""
SIMPLE ATTENDANCE SHEET GENERATION - REBUILT FROM SCRATCH
Clean, working implementation
"""
from supabase_client import supabase
from app.database import USE_SUPABASE_DB
from helpers.utils import extract_semester_from_roll_no


def generate_attendance_sheet(course_code, exam_date, semester_id, **kwargs):
    """Generate attendance sheet HTML - SIMPLE VERSION"""
    try:
        # Get semester info
        sem_result = supabase.table('semesters').select('*').eq('id', semester_id).execute()
        if not sem_result.data:
            return None, "Semester not found"
        semester = sem_result.data[0]
        
        # Get students
        students_result = supabase.table('students').select('*').eq('semester_id', semester_id).eq('course_code', course_code).execute()
        if not students_result.data:
            return None, "No students found"
        
        students = students_result.data
        
        # Sort: Batch -> Semester -> Name
        def sort_key(s):
            batch = (s.get('timetable_batch') or 'ZZZ').upper()
            semester = extract_semester_from_roll_no(s.get('roll_no', ''))
            name = (s.get('name') or '').upper()
            return (batch, semester, name)
        
        students.sort(key=sort_key)
        
        # Get course info from first student
        course_title = students[0].get('course_title', 'Unknown Course')
        instructor = students[0].get('main_instructor', 'Unknown Instructor')
        
        # Generate HTML
        html = generate_html(course_code, course_title, instructor, exam_date, semester, students)
        
        return html, "Success"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


def generate_html(course_code, course_title, instructor, exam_date, semester, students):
    """Generate the HTML content"""
    
    # Map semester types
    sem_type = {'monsoon': 'Monsoon', 'winter': 'Winter'}.get(semester.get('semester_type', ''), semester.get('semester_type', ''))
    exam_type = {'midsem': 'Mid Semester Examination', 'endsem': 'End Semester Examination'}.get(semester.get('exam_type', ''), semester.get('exam_type', ''))
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Attendance - {course_code}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 10px; }}
        .header div {{ margin: 3px 0; }}
        .bold {{ font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid black; padding: 5px; font-size: 11px; }}
        th {{ background-color: #f0f0f0; }}
        @media print {{ body {{ margin: 10mm; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="bold" style="font-size: 14px;">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
        <div class="bold" style="font-size: 12px;">DEPARTMENT OF MECHANICAL ENGINEERING</div>
        <div class="bold" style="font-size: 12px;">Statement of Answer Books and Bio breaks Details</div>
    </div>

    <div style="font-size: 11px; margin: 10px 0;">
        <div><strong>Examination:</strong> {exam_type}</div>
        <div>
            <strong>Semester:</strong> {sem_type} &nbsp;&nbsp;
            <strong>Academic Year:</strong> {semester.get('academic_year', '')} &nbsp;&nbsp;
            <strong>Date:</strong> {exam_date}
        </div>
        <div>
            <strong>Course Code:</strong> {course_code} &nbsp;&nbsp;
            <strong>Course Name:</strong> {course_title} &nbsp;&nbsp;
            <strong>Instructor:</strong> {instructor}
        </div>
    </div>

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
    
    # Add student rows
    for i, student in enumerate(students, 1):
        roll = student.get('roll_no', '')
        name = student.get('name', '')
        batch = student.get('timetable_batch', '') or '-'
        
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
