"""Test script to generate absentee HTML locally"""
import sys
import os

# Mock the necessary variables
class MockSupabase:
    pass

# Add to globals
supabase = None
USE_SUPABASE_DB = False

# Simple test data
test_absentees = [
    {
        'roll_no': 'B230396ME',
        'name': 'LAUDYAVATH BHANUCHANDER',
        'course_code': 'ME3411E',
        'course_title': 'Machine Design',
        'exam_date': '2026-02-22',
        'instructor': '1166-Ilango M',
        'academic_year': '2025-26',
        'semester_type': 'winter',
        'exam_type': 'midsem',
        'timetable_batch': 'ME02'
    },
    {
        'roll_no': 'B230397ME',
        'name': 'LEO JOSEPH',
        'course_code': 'ME3411E',
        'course_title': 'Machine Design',
        'exam_date': '2026-02-22',
        'instructor': '1166-Ilango M',
        'academic_year': '2025-26',
        'semester_type': 'winter',
        'exam_type': 'midsem',
        'timetable_batch': 'ME02'
    },
    {
        'roll_no': 'B230401ME',
        'name': 'MAAHIRA SINHA',
        'course_code': 'ME3411E',
        'course_title': 'Machine Design',
        'exam_date': '2026-02-22',
        'instructor': '1166-Ilango M',
        'academic_year': '2025-26',
        'semester_type': 'winter',
        'exam_type': 'midsem',
        'timetable_batch': 'ME02'
    }
]

# Import the function
from datetime import datetime
from collections import defaultdict
from helpers.utils import sort_by_roll_number

def generate_test_html(absentees):
    """Generate HTML - simplified version"""
    
    # Group by course
    grouped = defaultdict(list)
    for absentee in absentees:
        key = (
            absentee.get('course_code', ''),
            absentee.get('exam_date', ''),
            absentee.get('instructor', ''),
            absentee.get('course_title', ''),
            absentee.get('academic_year', ''),
            absentee.get('semester_type', ''),
            absentee.get('exam_type', '')
        )
        grouped[key].append(absentee)
    
    sorted_courses = sorted(grouped.items(), key=lambda x: (x[0][1], x[0][0]))
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Consolidated Absentee List</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 10px; 
        }
        .institute-name { 
            font-weight: bold; 
            font-size: 14px; 
        }
        .department { 
            font-weight: bold; 
            font-size: 12px; 
            margin-top: 3px; 
        }
        .form-title { 
            font-weight: bold; 
            font-size: 12px; 
            margin-top: 6px; 
        }
        .page-no { 
            font-size: 10px; 
            margin-top: 4px; 
        }
        .info-section {
            margin: 10px 0;
            font-size: 10px;
        }
        .info-section div {
            margin: 3px 0;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 8px 0; 
        }
        th, td { 
            border: 1px solid black; 
            padding: 4px; 
            text-align: left; 
            font-size: 10px; 
        }
        th { 
            background-color: #f0f0f0; 
            font-weight: bold; 
        }
    </style>
</head>
<body>
"""
    
    for course_key, course_absentees in sorted_courses:
        course_code, exam_date, instructor, course_title, academic_year, semester_type, exam_type = course_key
        
        sorted_absentees = sorted(course_absentees, key=lambda x: x.get('roll_no', ''))
        
        rows_per_page = 60
        total_students = len(sorted_absentees)
        total_pages = 1
        
        formatted_exam_date = datetime.strptime(str(exam_date), '%Y-%m-%d').strftime('%d-%m-%Y')
        exam_type_text = 'Mid Semester Examination'
        semester_text = 'Winter'
        
        html_content += f"""
    <div class="page">
        <div class="header">
            <div class="institute-name">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
            <div class="department">DEPARTMENT OF MECHANICAL ENGINEERING</div>
            <div class="form-title">Statement of Answer Books and Bio breaks Details</div>
            <div class="page-no">Page 1 of 1</div>
        </div>

        <div class="info-section">
            <div><strong>Name of the Examination:</strong> {exam_type_text}</div>
            <div>
                <strong>Semester:</strong> {semester_text} &nbsp;&nbsp;
                <strong>Academic Year:</strong> {academic_year} &nbsp;&nbsp;
                <strong>Date:</strong> {formatted_exam_date} &nbsp;&nbsp;
                <strong>Time:</strong> ____________
            </div>
            <div>
                <strong>Course Code:</strong> {course_code} &nbsp;&nbsp;
                <strong>Course Name:</strong> {course_title} &nbsp;&nbsp;
                <strong>Instructor:</strong> {instructor}
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">Sl. No.</th>
                    <th style="width: 12%;">Roll No.</th>
                    <th style="width: 7%;">Batch</th>
                    <th style="width: 32%;">Student Name</th>
                    <th style="width: 13%;">No. of Additional Sheets</th>
                    <th style="width: 16%;">Details of Bio Break</th>
                    <th style="width: 15%;">Signature</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for i, student in enumerate(sorted_absentees):
            serial_no = i + 1
            roll_no = student.get('roll_no', '')
            name = student.get('name', '')
            batch = student.get('timetable_batch', '')
            
            html_content += f"""
                <tr>
                    <td>{serial_no}</td>
                    <td>{roll_no}</td>
                    <td>{batch}</td>
                    <td>{name}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                </tr>"""
        
        html_content += """
            </tbody>
        </table>

        <div style="margin-top: 20px;">
            <table>
                <tr>
                    <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of the answer Books</th>
                    <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of the Invigilators</th>
                </tr>
                <tr>
                    <td style="width: 12%;"></td>
                    <th style="width: 8%; text-align: center;">Main</th>
                    <th style="width: 13%; text-align: center;">Additional</th>
                    <th style="width: 10%; text-align: center;">Sl. No.</th>
                    <th style="width: 35%; text-align: center;">Name</th>
                    <th style="width: 22%; text-align: center;">Signature</th>
                </tr>
                <tr>
                    <td><strong>Received</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">1</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td><strong>Used</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">2</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td><strong>Balance</strong></td>
                    <td></td>
                    <td></td>
                    <td style="text-align: center;">3</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <th colspan="6" style="background-color: #d3d3d3; text-align: center;">Details of Absentees</th>
                </tr>
                <tr>
                    <th style="text-align: center;">No. of Absentees</th>
                    <td></td>
                    <th colspan="4" style="text-align: center;">Roll no. of Absentees</th>
                </tr>
            </table>
        </div>
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    return html_content


if __name__ == "__main__":
    print("Generating test absentee HTML...")
    html = generate_test_html(test_absentees)
    
    output_file = 'test_absentee_output.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Generated {output_file}")
    print(f"  HTML length: {len(html)} characters")
    print(f"\nPlease open {output_file} in your browser to see the result!")
