"""
Quick diagnostic script to check what data was uploaded
"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase

# Get the most recent semester
result = supabase.table('semesters').select('*').order('id', desc=True).limit(1).execute()
if result.data:
    semester = result.data[0]
    print(f"\n=== Most Recent Semester ===")
    print(f"ID: {semester['id']}")
    print(f"Academic Year: {semester['academic_year']}")
    print(f"Semester Type: {semester['semester_type']}")
    print(f"Degree Level: {semester['degree_level']}")
    print(f"Exam Type: {semester['exam_type']}")
    print(f"DB Name: {semester['db_name']}")
    
    semester_id = semester['id']
    
    # Get sample students
    students_result = supabase.table('students').select('roll_no, name, program_name, course_code, course_title').eq('semester_id', semester_id).limit(10).execute()
    
    print(f"\n=== Sample Students (first 10) ===")
    if students_result.data:
        for student in students_result.data:
            roll_prefix = student['roll_no'][0] if student['roll_no'] else 'N/A'
            print(f"Roll: {student['roll_no']} (starts with '{roll_prefix}') | Program: {student['program_name']} | Course: {student['course_code']} - {student['course_title']}")
    else:
        print("No students found!")
    
    # Get total count
    count_result = supabase.table('students').select('id', count='exact').eq('semester_id', semester_id).execute()
    print(f"\n=== Total Students: {count_result.count} ===")
    
    # Get unique courses
    courses_result = supabase.table('students').select('course_code, course_title').eq('semester_id', semester_id).execute()
    unique_courses = {}
    for row in courses_result.data:
        code = row['course_code']
        if code not in unique_courses:
            unique_courses[code] = row['course_title']
    
    print(f"\n=== Unique Courses: {len(unique_courses)} ===")
    for code, title in sorted(unique_courses.items())[:5]:
        print(f"- {code}: {title}")
    
    # Check roll number prefixes
    print(f"\n=== Roll Number Analysis ===")
    prefix_counts = {}
    for student in students_result.data:
        if student['roll_no']:
            prefix = student['roll_no'][0].upper()
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    for prefix, count in sorted(prefix_counts.items()):
        level = {'B': 'UG', 'M': 'PG', 'P': 'PhD'}.get(prefix, 'Unknown')
        print(f"Prefix '{prefix}' → {level}: {count} students (in sample)")
    
else:
    print("No semesters found in database!")
