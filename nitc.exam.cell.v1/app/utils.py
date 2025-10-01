import re

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