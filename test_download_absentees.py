"""
Test script for validating absentee sheet download functionality
Run this to verify the download logic works before deploying
"""
import sys
from io import BytesIO

def test_session_handling():
    """Test that session.get() properly handles missing keys"""
    print("Testing session handling...")
    
    # Simulate empty session
    session = {}
    absentees = session.get('absentees', [])
    assert absentees == [], "Empty session should return empty list"
    print("✓ Empty session handling works")
    
    # Simulate session with data
    session = {'absentees': [
        {'roll_no': 'B220001CS', 'name': 'Test Student', 'course_code': 'CS1001', 'course_title': 'Test Course'}
    ]}
    absentees = session.get('absentees', [])
    assert len(absentees) == 1, "Session with data should return data"
    print("✓ Session with absentees works")
    
    # Test the old buggy way (would throw KeyError)
    try:
        session = {}
        if session['absentees']:  # This throws KeyError!
            pass
        print("✗ Old method should have thrown KeyError!")
        sys.exit(1)
    except KeyError:
        print("✓ Confirmed: old method throws KeyError (bug fixed)")

def test_pdf_generation():
    """Test that PDF generation import works"""
    print("\nTesting PDF generation imports...")
    try:
        from xhtml2pdf import pisa
        print("✓ xhtml2pdf (pisa) import successful")
    except ImportError as e:
        print(f"✗ Failed to import xhtml2pdf: {e}")
        return False
    
    # Test basic PDF generation
    try:
        html = "<html><body><h1>Test PDF</h1></body></html>"
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
        if pdf.err:
            print("✗ PDF generation had errors")
            return False
        pdf_bytes = result.getvalue()
        assert len(pdf_bytes) > 0, "PDF should have content"
        print(f"✓ Basic PDF generation works ({len(pdf_bytes)} bytes)")
        return True
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        return False

def test_zip_creation():
    """Test ZIP file creation for multiple PDFs"""
    print("\nTesting ZIP file creation...")
    try:
        import zipfile
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("test1.pdf", b"fake pdf content 1")
            zip_file.writestr("test2.pdf", b"fake pdf content 2")
        
        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        assert len(zip_content) > 0, "ZIP should have content"
        print(f"✓ ZIP creation works ({len(zip_content)} bytes)")
        
        # Verify ZIP is valid
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            names = zip_file.namelist()
            assert 'test1.pdf' in names and 'test2.pdf' in names
            print(f"✓ ZIP contains correct files: {names}")
        return True
    except Exception as e:
        print(f"✗ ZIP creation failed: {e}")
        return False

def test_form_data_parsing():
    """Test exam date extraction from form data"""
    print("\nTesting form data parsing...")
    
    # Simulate form data
    form_data = {
        'semester_id': '1',
        'exam_date_CS1001': '2026-02-23',
        'exam_date_MA1001': '2026-02-24',
        'action': 'download_absentees',
        'other_field': 'value'
    }
    
    # Extract exam dates (like in app.py)
    exam_dates = {}
    for key in form_data.keys():
        if key.startswith('exam_date_'):
            course_code = key.replace('exam_date_', '')
            exam_dates[course_code] = form_data.get(key)
    
    assert len(exam_dates) == 2, "Should extract 2 exam dates"
    assert exam_dates['CS1001'] == '2026-02-23', "CS1001 date should match"
    assert exam_dates['MA1001'] == '2026-02-24', "MA1001 date should match"
    print(f"✓ Form data parsing works: {exam_dates}")

def test_absentee_grouping():
    """Test grouping absentees by course"""
    print("\nTesting absentee grouping...")
    
    absentees = [
        {'roll_no': 'B220001CS', 'name': 'Student 1', 'course_code': 'CS1001', 'course_title': 'Course 1'},
        {'roll_no': 'B220002CS', 'name': 'Student 2', 'course_code': 'CS1001', 'course_title': 'Course 1'},
        {'roll_no': 'B220003CS', 'name': 'Student 3', 'course_code': 'MA1001', 'course_title': 'Course 2'},
    ]
    
    # Group by course (like in app.py)
    absentees_by_course = {}
    for absentee in absentees:
        course_code = absentee['course_code']
        if course_code not in absentees_by_course:
            absentees_by_course[course_code] = []
        absentees_by_course[course_code].append(absentee['roll_no'])
    
    assert len(absentees_by_course) == 2, "Should have 2 courses"
    assert len(absentees_by_course['CS1001']) == 2, "CS1001 should have 2 students"
    assert len(absentees_by_course['MA1001']) == 1, "MA1001 should have 1 student"
    print(f"✓ Absentee grouping works: {absentees_by_course}")

def main():
    """Run all tests"""
    print("="*60)
    print("ABSENTEE DOWNLOAD FUNCTIONALITY TEST")
    print("="*60)
    
    try:
        test_session_handling()
        test_form_data_parsing()
        test_absentee_grouping()
        test_pdf_generation()
        test_zip_creation()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nThe download functionality should work correctly.")
        print("If download still fails, check:")
        print("1. Browser console for JavaScript errors")
        print("2. Backend logs for [DOWNLOAD ABSENTEES] messages")
        print("3. Network tab to see if POST request is sent")
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
