"""Quick script to debug what HTML is being generated for approved absentees"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules
from supabase_client import supabase
from config import USE_SUPABASE_DB

if __name__ == "__main__":
    print("=" * 80)
    print("DEBUGGING APPROVED ABSENTEES HTML GENERATION")
    print("=" * 80)
    
    # Get approved absentees
    print("\n1. Fetching approved absentees from database...")
    result = supabase.table('absentees')\
        .select('*, semesters(academic_year, semester_type, exam_type)')\
        .eq('status', 'approved')\
        .execute()
    
    print(f"   Found {len(result.data) if result.data else 0} approved absentees")
    
    if result.data:
        print("\n2. Sample absentee record:")
        sample = result.data[0]
        print(f"   Roll No: {sample.get('roll_no')}")
        print(f"   Name: {sample.get('name')}")
        print(f"   Course Code: {sample.get('course_code')}")
        print(f"   Course Title: {sample.get('course_title')}")
        print(f"   Exam Date: {sample.get('exam_date')} (type: {type(sample.get('exam_date'))})")
        print(f"   Semesters: {sample.get('semesters')}")
        
        # Format exam_date
        exam_date = sample.get('exam_date')
        if exam_date:
            if hasattr(exam_date, 'strftime'):
                formatted = exam_date.strftime('%Y-%m-%d')
                print(f"   Formatted (from datetime): {formatted}")
            elif isinstance(exam_date, str):
                formatted = str(exam_date).split('T')[0] if 'T' in str(exam_date) else str(exam_date)
                print(f"   Formatted (from string): {formatted}")
        
        print("\n3. Enriching with instructor data...")
        for absentee in result.data[:3]:  # Just check first 3
            course_code = absentee.get('course_code', '')
            student_query = supabase.table('students')\
                .select('main_instructor')\
                .eq('course_code', course_code)\
                .limit(1)\
                .execute()
            instructor = student_query.data[0].get('main_instructor', 'N/A') if student_query.data else 'N/A'
            print(f"   {course_code}: Instructor = {instructor}")
        
        print("\n4. Generating HTML...")
        # Import the function
        from app import generate_consolidated_absentee_html
        
        # Prepare data (flatten semester info)
        for absentee in result.data:
            # Ensure exam_date is properly formatted
            exam_date = absentee.get('exam_date')
            if exam_date:
                if hasattr(exam_date, 'strftime'):
                    absentee['exam_date'] = exam_date.strftime('%Y-%m-%d')
                elif isinstance(exam_date, str):
                    absentee['exam_date'] = str(exam_date).split('T')[0] if 'T' in str(exam_date) else str(exam_date)
            
            # Flatten semester data
            if absentee.get('semesters'):
                absentee['academic_year'] = absentee['semesters'].get('academic_year', '')
                absentee['semester_type'] = absentee['semesters'].get('semester_type', '')
                absentee['exam_type'] = absentee['semesters'].get('exam_type', '')
            else:
                absentee['academic_year'] = ''
                absentee['semester_type'] = ''
                absentee['exam_type'] = ''
            
            # Get instructor data
            student_query = supabase.table('students')\
                .select('main_instructor')\
                .eq('course_code', absentee.get('course_code', ''))\
                .limit(1)\
                .execute()
            if student_query.data:
                absentee['instructor'] = student_query.data[0].get('main_instructor', 'N/A')
            else:
                absentee['instructor'] = 'N/A'
        
        html_content = generate_consolidated_absentee_html(result.data)
        
        # Save HTML to file
        output_file = 'debug_approved_absentees.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✓ HTML saved to: {output_file}")
        print(f"   HTML length: {len(html_content)} characters")
        print(f"\n   First 500 characters:")
        print(f"   {html_content[:500]}")
    else:
        print("   ⚠ No approved absentees found in database!")
    
    print("\n" + "=" * 80)
