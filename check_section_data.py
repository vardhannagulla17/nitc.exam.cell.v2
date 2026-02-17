"""
Check if section column has data and what format it's in
"""
from supabase_client import supabase

# Check a sample of students to see if section column exists and has data
print("Checking section data in students table...\n")

# Get a sample of students from a specific course
result = supabase.table('students').select('roll_no, name, course_code, section, timetable_batch').eq('course_code', 'ME3411E').limit(10).execute()

if result.data:
    print(f"Found {len(result.data)} students in ME3411E")
    print("\nSample data:")
    for student in result.data:
        print(f"  Roll: {student['roll_no']}")
        print(f"  Name: {student['name']}")
        print(f"  Section: {student.get('section', 'NULL')}")
        print(f"  Timetable Batch: {student.get('timetable_batch', 'NULL')}")
        print()
    
    # Check if section column has any data
    sections_with_data = [s for s in result.data if s.get('section')]
    print(f"\nStudents with section data: {len(sections_with_data)} out of {len(result.data)}")
    
    # Check timetable_batch values
    unique_batches = set(s.get('timetable_batch') for s in result.data if s.get('timetable_batch'))
    print(f"Unique timetable_batch values: {unique_batches}")
else:
    print("No students found in ME3411E")

# Check total students in database
total_result = supabase.table('students').select('id', count='exact').execute()
print(f"\nTotal students in database: {total_result.count}")

# Check if section column exists by checking schema
print("\nChecking if section column exists...")
sample = supabase.table('students').select('*').limit(1).execute()
if sample.data:
    print(f"Available columns: {list(sample.data[0].keys())}")
