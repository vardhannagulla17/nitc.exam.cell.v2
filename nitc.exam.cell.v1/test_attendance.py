#!/usr/bin/env python3
"""Test script to generate a sample attendance sheet"""

import sqlite3
import os
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

def test_attendance_generation():
    """Generate a test attendance sheet"""
    try:
        conn = sqlite3.connect('exam_cell.db')
        cursor = conn.cursor()
        
        # Get students for a specific course
        course_code = 'MA6001E'
        cursor.execute('''
            SELECT roll_no, name, course_title, main_instructor, program_name 
            FROM students 
            WHERE course_code = ? 
            LIMIT 20
        ''', (course_code,))
        
        students = cursor.fetchall()
        conn.close()
        
        if not students:
            print("No students found!")
            return
        
        # Sort students by department then roll number
        students_sorted = sort_by_roll_number(students)
        
        print(f"Found {len(students_sorted)} students for course {course_code}")
        print("Students sorted by department:")
        for i, student in enumerate(students_sorted, 1):
            dept = student[0][-2:] if student[0] and len(student[0]) >= 2 else 'XX'
            print(f"{i:2d}. {student[0]:12s} ({dept}) - {student[1]}")
        
        print(f"\nCourse: {students_sorted[0][2]}")
        print(f"Instructor: {students_sorted[0][3]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_attendance_generation()
