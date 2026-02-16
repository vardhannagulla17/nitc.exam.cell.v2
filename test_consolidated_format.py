"""
Test consolidated absentee list format
"""

# Sample absentee data
sample_absentees = [
    {'roll_no': 'B210001ME', 'name': 'STUDENT ONE', 'course_code': 'ME1011E', 'course_title': 'Engineering Graphics', 'exam_date': '2026-02-20'},
    {'roll_no': 'B210050CE', 'name': 'STUDENT TWO', 'course_code': 'CE2010E', 'course_title': 'Structural Analysis', 'exam_date': '2026-02-20'},
    {'roll_no': 'M210015ME', 'name': 'STUDENT THREE', 'course_code': 'ME6213E', 'course_title': 'Applied Thermodynamics', 'exam_date': '2026-02-20'},
    {'roll_no': 'B210025ME', 'name': 'STUDENT FOUR', 'course_code': 'ME1011E', 'course_title': 'Engineering Graphics', 'exam_date': '2026-02-20'},
    {'roll_no': 'B210003EE', 'name': 'STUDENT FIVE', 'course_code': 'EE3010E', 'course_title': 'Power Systems', 'exam_date': '2026-02-20'},
]

print("=== NEW CONSOLIDATED ABSENTEE LIST FORMAT ===\n")
print("The consolidated list will now show:\n")
print("+--------+---------------+------------------+----------------------------------------+")
print("| S.No   | Roll Number   | Student Name     | Course (Code - Title)                  |")
print("+--------+---------------+------------------+----------------------------------------+")

# Sort by roll number (simple sort for demonstration)
from helpers.utils import sort_by_roll_number
students_tuples = [(a['roll_no'], a['name'], a['course_code'], a['course_title']) for a in sample_absentees]
sorted_students = sort_by_roll_number(students_tuples)

for idx, student in enumerate(sorted_students, 1):
    roll_no, name, course_code, course_title = student
    print(f"| {idx:<6} | {roll_no:<13} | {name:<16} | {course_code} - {course_title:<20} |")

print("+--------+---------------+------------------+----------------------------------------+")
print(f"\nTotal Absentees: {len(sorted_students)}")
print("\nKey changes:")
print("- Single flat list (not grouped by course)")
print("- Sorted by roll number")
print("- Shows full course information in one column: 'Code - Title'")
print("- Easier to scan and verify")
