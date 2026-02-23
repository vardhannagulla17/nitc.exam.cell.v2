"""
Test script to debug attendance sheet download issues
"""
import os
os.environ['USE_SUPABASE_DB'] = 'True'

from app.attendance import generate_attendance_sheet, _get_students_for_course, _get_semester_info

def test_download():
    """Test attendance sheet generation"""
    print("\n" + "="*60)
    print("TESTING ATTENDANCE SHEET GENERATION")
    print("="*60 + "\n")
    
    # Test parameters - Update these with actual values from your database
    semester_id = input("Enter semester_id (e.g., 1): ").strip()
    course_code = input("Enter course_code (e.g., ME101): ").strip()
    exam_date = input("Enter exam_date (YYYY-MM-DD): ").strip()
    program_level = input("Enter program_level (UG/PG/PhD or leave blank): ").strip() or None
    
    print(f"\nTesting with:")
    print(f"  semester_id: {semester_id}")
    print(f"  course_code: {course_code}")
    print(f"  exam_date: {exam_date}")
    print(f"  program_level: {program_level}")
    print("\n" + "="*60 + "\n")
    
    # Test 1: Check semester info
    print("TEST 1: Getting semester info...")
    semester_info = _get_semester_info(semester_id)
    if semester_info:
        print(f"✓ Semester info: {semester_info}")
    else:
        print("✗ Semester not found!")
        return
    
    # Test 2: Check students
    print("\nTEST 2: Getting students...")
    students = _get_students_for_course(semester_id, course_code, program_level=program_level)
    print(f"Found {len(students)} students")
    
    if students:
        print(f"✓ First student: {students[0]}")
        print(f"  Keys: {list(students[0].keys())}")
    else:
        print("✗ No students found!")
        print("\nPossible reasons:")
        print("  1. No data in database for this course")
        print("  2. Supabase connection issue")
        print("  3. Incorrect semester_id or course_code")
        return
    
    # Test 3: Generate attendance sheet
    print("\nTEST 3: Generating attendance sheet...")
    html_content, message = generate_attendance_sheet(
        course_code=course_code,
        exam_date=exam_date,
        semester_id=semester_id,
        preview=True,
        program_level=program_level
    )
    
    if html_content:
        print(f"✓ Success! Generated {len(html_content)} chars of HTML")
        print(f"  Message: {message}")
        
        # Save to file for inspection
        output_file = "test_attendance_output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n✓ Saved to {output_file}")
    else:
        print(f"✗ Failed!")
        print(f"  Message: {message}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == '__main__':
    test_download()
