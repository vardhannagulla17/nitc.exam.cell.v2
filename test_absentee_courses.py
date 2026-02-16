"""
Test absentee sheet course loading
"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase

# Simulate what the absentee sheet does
print("=== Simulating Absentee Sheet Course Loading ===")

# Handle pagination - get all students
all_students = []
page_size = 1000
offset = 0

while True:
    response = supabase.table('students').select('course_code, course_title').range(offset, offset + page_size - 1).execute()
    if not response.data:
        break
    all_students.extend(response.data)
    print(f"Fetched page: offset={offset}, records={len(response.data)}")
    if len(response.data) < page_size:
        break
    offset += page_size

print(f"\nTotal student records fetched: {len(all_students)}")

# Create unique set of courses
unique_courses = {}
for row in all_students:
    code = row.get('course_code')
    title = row.get('course_title')
    if code and title and code not in unique_courses:
        unique_courses[code] = title

# Convert to sorted list
all_courses = sorted([(code, title) for code, title in unique_courses.items()])

print(f"Total unique courses: {len(all_courses)}")
print("\nFirst 10 courses:")
for code, title in all_courses[:10]:
    print(f"  {code}: {title}")

print("\nLast 10 courses:")
for code, title in all_courses[-10:]:
    print(f"  {code}: {title}")
