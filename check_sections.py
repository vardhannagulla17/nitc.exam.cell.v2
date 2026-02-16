"""
Check section/batch data structure
"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase

# Check what columns we have for sections/batches
print("=== Checking Section/Batch Data ===")

# Get a sample course with multiple sections
result = supabase.table('students').select('course_code, course_title, timetable_batch, main_instructor, roll_no, name').eq('course_code', 'ME3411E').limit(20).execute()

if result.data:
    print(f"\nFound {len(result.data)} students for ME3411E (Machine Design)")
    print("\nSample data:")
    
    # Group by batch
    batches = {}
    for student in result.data:
        batch = student.get('timetable_batch', 'N/A')
        instructor = student.get('main_instructor', 'N/A')
        if batch not in batches:
            batches[batch] = {'instructor': instructor, 'students': []}
        batches[batch]['students'].append(student['roll_no'])
    
    print(f"\nUnique batches/sections found: {list(batches.keys())}")
    for batch, info in sorted(batches.items()):
        print(f"\n{batch}:")
        print(f"  Instructor: {info['instructor']}")
        print(f"  Students: {len(info['students'])}")
        print(f"  Sample rolls: {', '.join(info['students'][:5])}")

# Check another course
print("\n" + "="*50)
result2 = supabase.table('students').select('course_code, timetable_batch, main_instructor').eq('course_code', 'ME1011E').execute()
if result2.data:
    batches2 = {}
    for student in result2.data:
        batch = student.get('timetable_batch', 'N/A')
        instructor = student.get('main_instructor', 'N/A')
        if batch not in batches2:
            batches2[batch] = {'instructor': instructor, 'count': 0}
        batches2[batch]['count'] += 1
    
    print(f"\nME1011E has {len(batches2)} sections/batches:")
    for batch, info in sorted(batches2.items()):
        print(f"  {batch}: {info['count']} students, Instructor: {info['instructor']}")
