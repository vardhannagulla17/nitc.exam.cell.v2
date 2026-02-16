"""
Test attendance sheet generation
"""
from dotenv import load_dotenv
load_dotenv()

# Set up Flask app context
from app import create_app
app = create_app()

with app.app_context():
    from app.attendance import generate_attendance_sheet
    from supabase_client import supabase
    
    # Get the semester ID
    semester_id = 2  # From previous test
    course_code = 'ME1011E'
    exam_date = '2026-01-15'
    
    print(f"=== Testing Attendance Sheet Generation ===")
    print(f"Semester ID: {semester_id}")
    print(f"Course: {course_code}")
    print(f"Exam Date: {exam_date}")
    
    # Test 1: Generate WITHOUT program level filter
    print(f"\n=== Test 1: Generate WITHOUT program level filter ===")
    html_content, message = generate_attendance_sheet(
        course_code=course_code,
        exam_date=exam_date,
        semester_id=semester_id,
        preview=True,
        program_level=None
    )
    print(f"Result: {message}")
    if html_content:
        print(f"HTML length: {len(html_content)} characters")
        # Check if it has students
        if 'B230804ME' in html_content:
            print("✅ Contains first student (B230804ME)")
        if 'B251442PE' in html_content:
            print("✅ Contains last student (B251442PE)")
    else:
        print("❌ No HTML generated")
    
    # Test 2: Generate WITH UG program level filter
    print(f"\n=== Test 2: Generate WITH UG program level filter ===")
    html_content_ug, message_ug = generate_attendance_sheet(
        course_code=course_code,
        exam_date=exam_date,
        semester_id=semester_id,
        preview=True,
        program_level='UG'
    )
    print(f"Result: {message_ug}")
    if html_content_ug:
        print(f"HTML length: {len(html_content_ug)} characters")
        # Check if it has students
        if 'B230804ME' in html_content_ug:
            print("✅ Contains first student (B230804ME)")
        if 'B251442PE' in html_content_ug:
            print("✅ Contains last student (B251442PE)")
    else:
        print("❌ No HTML generated")
    
    # Compare results
    print(f"\n=== Comparison ===")
    print(f"Without filter - HTML length: {len(html_content) if html_content else 0}")
    print(f"With UG filter - HTML length: {len(html_content_ug) if html_content_ug else 0}")
    
    # Test 3: Try with a PG course if available
    print(f"\n=== Test 3: Check if PG courses work ===")
    pg_result = supabase.table('students').select('course_code').eq('semester_id', semester_id).like('roll_no', 'M%').limit(1).execute()
    if pg_result.data:
        pg_course = pg_result.data[0]['course_code']
        print(f"Found PG course: {pg_course}")
        html_pg, message_pg = generate_attendance_sheet(
            course_code=pg_course,
            exam_date=exam_date,
            semester_id=semester_id,
            preview=True,
            program_level='PG'
        )
        print(f"PG Result: {message_pg}")
        if html_pg:
            print(f"✅ PG HTML generated: {len(html_pg)} characters")
        else:
            print("❌ No PG HTML generated")
    else:
        print("No PG courses found")

