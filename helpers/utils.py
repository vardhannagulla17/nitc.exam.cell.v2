import re
from datetime import datetime

def extract_semester_from_roll_no(roll_no):
    """
    Calculate current semester number from roll number based on admission year.
    Examples: B220001ME -> admitted 2022 -> calculate current semester
              M230045CS -> admitted 2023 -> calculate current semester
              P210002EE -> admitted 2021 -> calculate current semester
    
    Returns semester number (1, 2, 3, ...) based on current date.
    """
    if not roll_no:
        return 99  # Put invalid roll numbers at the end
    
    roll_str = str(roll_no).strip().upper()
    
    # Extract year from roll number (typically positions 1-3)
    # Pattern: [Program Letter][2-digit year][number][dept code]
    year_match = re.search(r'^[A-Z](\d{2})', roll_str)
    if not year_match:
        return 99  # Invalid pattern
    
    # Get admission year
    year_2digit = int(year_match.group(1))
    admission_year = 2000 + year_2digit if year_2digit < 50 else 1900 + year_2digit
    
    # Get current date and determine current semester
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # Calculate years since admission
    years_since_admission = current_year - admission_year
    
    # Determine current semester:
    # Indian academic year typically has 2 semesters:
    # - Monsoon (odd): July/Aug - Nov/Dec
    # - Winter (even): Jan - May
    if current_month >= 7:  # July onwards = Monsoon semester (odd)
        current_semester = years_since_admission * 2 + 1
    else:  # Jan-June = Winter semester (even)
        current_semester = years_since_admission * 2
    
    # Ensure semester is at least 1
    return max(1, current_semester)

def sort_absentees_by_semester_batch_name(absentees_data):
    """
    Sort absentees by:
    1. Semester (increasing order) - calculated from roll number and current date
    2. Batch (e.g., ME01, ME02, CS01, etc.) - from timetable_batch field
    3. Name (alphabetically A-Z)
    
    Args:
        absentees_data: List of dicts with keys: roll_no, name, timetable_batch (optional)
    
    Returns:
        Sorted list
    """
    def sort_key(absentee):
        # Extract current semester from roll number
        semester = extract_semester_from_roll_no(absentee.get('roll_no', ''))
        
        # Get batch (timetable_batch field) - handle None/empty values
        batch = absentee.get('timetable_batch', '') or ''
        batch = batch.strip().upper() if batch else 'ZZ99'  # Default for missing batch
        
        # Get name for alphabetical sorting
        name = absentee.get('name', '').strip().upper()
        
        return (semester, batch, name)
    
    return sorted(absentees_data, key=sort_key)

def sort_attendance_students(students):
    """
    Sort attendance students by:
    1. Semester (increasing order) - calculated from roll number
    2. Batch (alphabetically) - from timetable_batch
    3. Name (alphabetically A-Z)
    
    Args:
        students: List of tuples (roll_no, name, course_title, main_instructor, program_name, timetable_batch)
    
    Returns:
        Sorted list
    """
    def sort_key(student):
        roll_no = student[0] if len(student) > 0 else ''
        name = student[1] if len(student) > 1 else ''
        timetable_batch = student[5] if len(student) > 5 else ''
        
        # Calculate current semester from roll number
        semester = extract_semester_from_roll_no(roll_no)
        
        # Get batch - handle None/empty values
        batch = timetable_batch or ''
        batch = batch.strip().upper() if batch else 'ZZ99'  # Default for missing batch
        
        # Get name for alphabetical sorting
        name_upper = name.strip().upper() if name else ''
        
        return (semester, batch, name_upper)
    
    return sorted(students, key=sort_key)

def sort_by_roll_number(students):
    """Sort students by department (last 2 letters) first, then by roll number"""
    def extract_sort_key(roll_no):
        if not roll_no:
            return ('ZZ', 0, '')
        roll_str = str(roll_no).strip()
        
        # Extract department (last 2 letters)
        department = roll_str[-2:] if len(roll_str) >= 2 else 'ZZ'
        
        # Extract numeric part for sorting within department
        numeric_match = re.search(r'\d+', roll_str)
        if numeric_match:
            return (department, int(numeric_match.group()), roll_str)
        return (department, 0, roll_str)
    
    # Sort students based on roll number
    return sorted(students, key=lambda x: extract_sort_key(x[0]))
