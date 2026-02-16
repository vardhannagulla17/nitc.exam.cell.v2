"""
Check all courses loaded in the database
"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase

# Get the most recent semester
result = supabase.table('semesters').select('*').order('id', desc=True).limit(1).execute()
semester = result.data[0]
semester_id = semester['id']

print(f"=== Semester Info ===")
print(f"ID: {semester_id}")
print(f"Academic Year: {semester['academic_year']}")
print(f"Semester Type: {semester['semester_type']}")
print(f"Degree Level: {semester['degree_level']}")

# Get ALL unique courses (raw query) - need to handle pagination
# Supabase has default limit of 1000, need to get all records
all_students_data = []
page_size = 1000
offset = 0

while True:
    result = supabase.table('students').select('course_code, course_title, roll_no, program_name').eq('semester_id', semester_id).range(offset, offset + page_size - 1).execute()
    if not result.data:
        break
    all_students_data.extend(result.data)
    if len(result.data) < page_size:
        break
    offset += page_size

# Create a mock result object
class MockResult:
    def __init__(self, data):
        self.data = data

all_students = MockResult(all_students_data)

print(f"\n=== Total Students: {len(all_students.data)} ===")

# Group by course
courses_dict = {}
for student in all_students.data:
    code = student['course_code']
    if code not in courses_dict:
        courses_dict[code] = {
            'title': student['course_title'],
            'students': [],
            'ug_count': 0,
            'pg_count': 0,
            'phd_count': 0
        }
    courses_dict[code]['students'].append(student['roll_no'])
    
    # Count by program level
    roll = student['roll_no']
    if roll:
        prefix = roll[0].upper()
        if prefix == 'B':
            courses_dict[code]['ug_count'] += 1
        elif prefix == 'M':
            courses_dict[code]['pg_count'] += 1
        elif prefix == 'P':
            courses_dict[code]['phd_count'] += 1

print(f"\n=== Total Unique Courses: {len(courses_dict)} ===")

# Separate by program level
ug_courses = {code: info for code, info in courses_dict.items() if info['ug_count'] > 0}
pg_courses = {code: info for code, info in courses_dict.items() if info['pg_count'] > 0}
phd_courses = {code: info for code, info in courses_dict.items() if info['phd_count'] > 0}

print(f"\nUG Courses (B-prefix students): {len(ug_courses)}")
print(f"PG Courses (M-prefix students): {len(pg_courses)}")
print(f"PhD Courses (P-prefix students): {len(phd_courses)}")

print(f"\n=== UG Courses Detail ===")
for code in sorted(ug_courses.keys()):
    info = ug_courses[code]
    print(f"{code}: {info['title']}")
    print(f"  UG students: {info['ug_count']}, PG: {info['pg_count']}, PhD: {info['phd_count']}")

print(f"\n=== Sample PG Courses (first 10) ===")
for i, code in enumerate(sorted(pg_courses.keys())[:10]):
    info = pg_courses[code]
    print(f"{code}: {info['title'][:50]}")
    print(f"  UG students: {info['ug_count']}, PG: {info['pg_count']}, PhD: {info['phd_count']}")

# Check for any courses with mixed program levels
print(f"\n=== Courses with Mixed Program Levels ===")
mixed_courses = {code: info for code, info in courses_dict.items() 
                 if (info['ug_count'] > 0 and info['pg_count'] > 0) or 
                    (info['ug_count'] > 0 and info['phd_count'] > 0) or
                    (info['pg_count'] > 0 and info['phd_count'] > 0)}
print(f"Found {len(mixed_courses)} courses with multiple program levels:")
for code in sorted(mixed_courses.keys()):
    info = mixed_courses[code]
    print(f"{code}: UG={info['ug_count']}, PG={info['pg_count']}, PhD={info['phd_count']}")

# Check roll number distribution
print(f"\n=== Roll Number Prefix Distribution ===")
prefix_counts = {'B': 0, 'M': 0, 'P': 0, 'Other': 0}
for student in all_students.data:
    roll = student['roll_no']
    if roll:
        prefix = roll[0].upper()
        if prefix in prefix_counts:
            prefix_counts[prefix] += 1
        else:
            prefix_counts['Other'] += 1

for prefix, count in prefix_counts.items():
    level = {'B': 'UG', 'M': 'PG', 'P': 'PhD', 'Other': 'Unknown'}.get(prefix, prefix)
    print(f"{prefix} ({level}): {count} students")
