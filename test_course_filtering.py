"""
Test course retrieval and filtering
"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase
from app.models import get_courses_for_semester
from app.attendance import get_sorted_students

# Get the most recent semester
result = supabase.table('semesters').select('id, academic_year, semester_type, degree_level').order('id', desc=True).limit(1).execute()
semester_id = result.data[0]['id']

print(f"Semester ID: {semester_id}")
print(f"Semester: {result.data[0]['academic_year']} {result.data[0]['semester_type']} {result.data[0]['degree_level']}")

# Test 1: Get courses WITHOUT program level filter
print(f"\n=== Test 1: Get courses WITHOUT program level filter ===")
courses_all = get_courses_for_semester(semester_id, program_level=None)
print(f"Found {len(courses_all)} courses:")
for code, title in courses_all[:5]:
    print(f"  - {code}: {title}")

# Test 2: Get courses WITH UG program level filter
print(f"\n=== Test 2: Get courses WITH UG program level filter ===")
courses_ug = get_courses_for_semester(semester_id, program_level='UG')
print(f"Found {len(courses_ug)} courses:")
for code, title in courses_ug[:5]:
    print(f"  - {code}: {title}")

# Test 3: Get students for a specific course WITHOUT filter
print(f"\n=== Test 3: Get students for ME1011E WITHOUT program level filter ===")
students_all = get_sorted_students(semester_id, 'ME1011E', program_level=None)
print(f"Found {len(students_all)} students")
if students_all:
    print(f"First student: {students_all[0]}")
    print(f"Last student: {students_all[-1]}")

# Test 4: Get students for a specific course WITH UG filter
print(f"\n=== Test 4: Get students for ME1011E WITH UG program level filter ===")
students_ug = get_sorted_students(semester_id, 'ME1011E', program_level='UG')
print(f"Found {len(students_ug)} students")
if students_ug:
    print(f"First student: {students_ug[0]}")
    print(f"Last student: {students_ug[-1]}")

# Test 5: Try with different program levels to see if that's the issue
print(f"\n=== Test 5: Get courses with different program levels ===")
for prog_level in ['UG', 'PG', 'PhD']:
    courses = get_courses_for_semester(semester_id, program_level=prog_level)
    print(f"{prog_level}: {len(courses)} courses")
