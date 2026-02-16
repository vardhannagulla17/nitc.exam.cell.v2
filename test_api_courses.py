"""
Test API endpoint for courses
"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

with app.app_context():
    from app.models import get_courses_for_semester, get_all_semesters
    from supabase_client import supabase
    
    # Get all semesters
    print("=== All Semesters ===")
    semesters = get_all_semesters()
    for sem in semesters:
        print(f"ID: {sem[0]}, Year: {sem[1]}, Type: {sem[2]}, Level: {sem[3]}, Exam: {sem[4]}")
    
    # Test with semester_id=2 and program_level=UG
    print("\n=== Testing: semester_id=2, program_level=UG ===")
    courses = get_courses_for_semester(2, 'UG')
    print(f"Found {len(courses)} courses:")
    for code, title in courses[:10]:
        print(f"  {code}: {title}")
    
    # Test with semester_id=1 and program_level=UG (the one in screenshot)
    print("\n=== Testing: semester_id=1, program_level=UG ===")
    courses_1 = get_courses_for_semester(1, 'UG')
    print(f"Found {len(courses_1)} courses:")
    for code, title in courses_1[:10]:
        print(f"  {code}: {title}")
    
    # Check what students exist for ME6323E (one of the courses shown in screenshot)
    print("\n=== Check ME6323E students ===")
    result = supabase.table('students').select('roll_no, semester_id').eq('course_code', 'ME6323E').limit(5).execute()
    if result.data:
        for student in result.data:
            prefix = student['roll_no'][0] if student['roll_no'] else 'N/A'
            level = {'B': 'UG', 'M': 'PG', 'P': 'PhD'}.get(prefix, 'Unknown')
            print(f"  Roll: {student['roll_no']} (Prefix: {prefix} = {level}), Semester: {student['semester_id']}")
    else:
        print("  No students found for ME6323E")
    
    # Check which semester has ME6323E
    print("\n=== Find which semester has ME6323E ===")
    result = supabase.table('students').select('semester_id').eq('course_code', 'ME6323E').limit(1).execute()
    if result.data:
        sem_id = result.data[0]['semester_id']
        print(f"ME6323E is in semester_id={sem_id}")
        
        # Get that semester's info
        sem_result = supabase.table('semesters').select('*').eq('id', sem_id).execute()
        if sem_result.data:
            sem = sem_result.data[0]
            print(f"Semester {sem_id}: {sem['academic_year']} {sem['semester_type']} {sem['degree_level']} {sem['exam_type']}")
