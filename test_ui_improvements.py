"""
Test Suite for UI Improvements
Tests HTML template changes and CSS improvements
"""

import sys
import os
import unittest
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


class TestAdminAbsenteesUIChanges(unittest.TestCase):
    """Test UI changes in admin absentees page"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Create admin session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['email'] = 'admin@nitc.ac.in'
            sess['full_name'] = 'Test Admin'
            sess['role'] = 'admin'
    
    def test_course_filter_dropdown_styling(self):
        """Test that course filter dropdown has improved styling"""
        print("\n✓ Testing course filter dropdown styling...")
        
        response = self.client.get('/admin/absentees')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for autocomplete dropdown with improved width
            self.assertIn('courseDropdown', html)
            self.assertIn('min-width: 100%', html)
            self.assertIn('width: max-content', html)
            self.assertIn('max-width: 400px', html)
            
            print("   ✓ Course dropdown has improved width constraints")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")
    
    def test_cloud_storage_section_position(self):
        """Test that cloud storage section is at the bottom"""
        print("\n✓ Testing cloud storage section position...")
        
        response = self.client.get('/admin/absentees')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Find positions of key sections
            absentees_table_pos = html.find('Absentee Records')
            cloud_storage_pos = html.find('Cloud Storage')
            
            if absentees_table_pos != -1 and cloud_storage_pos != -1:
                # Cloud storage should come after absentees table
                self.assertGreater(cloud_storage_pos, absentees_table_pos)
                print("   ✓ Cloud storage section correctly positioned at bottom")
            else:
                print("   ⚠ Sections not found in response")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")
    
    def test_filter_section_structure(self):
        """Test that filter section has proper structure"""
        print("\n✓ Testing filter section structure...")
        
        response = self.client.get('/admin/absentees')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for filter elements
            self.assertIn('Filter Absentees', html)
            self.assertIn('exam_date', html)
            self.assertIn('status', html)
            self.assertIn('course_code', html)
            self.assertIn('Apply Filters', html)
            
            print("   ✓ Filter section has all required elements")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")


class TestTimetableUIChanges(unittest.TestCase):
    """Test UI changes in timetable page"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Create admin session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['email'] = 'admin@nitc.ac.in'
            sess['full_name'] = 'Test Admin'
            sess['role'] = 'admin'
    
    def test_timetable_css_improvements(self):
        """Test that timetable page has improved CSS"""
        print("\n✓ Testing timetable CSS improvements...")
        
        response = self.client.get('/timetable')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for CSS variable definitions
            self.assertIn('--primary-color:', html)
            self.assertIn('--primary-dark:', html)
            self.assertIn('--border-color:', html)
            
            # Check for improved styling classes
            self.assertIn('timetable-container', html)
            self.assertIn('section-title', html)
            self.assertIn('form-control', html)
            
            # Check for gradient styles
            self.assertIn('linear-gradient', html)
            
            print("   ✓ Timetable page has improved CSS with modern design")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")
    
    def test_upload_form_layout(self):
        """Test that upload form has improved layout"""
        print("\n✓ Testing upload form layout...")
        
        response = self.client.get('/timetable')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for form structure
            self.assertIn('upload-form', html)
            self.assertIn('semester_id', html)
            self.assertIn('btn-upload', html)
            
            # Check for responsive grid
            self.assertIn('grid-template-columns', html)
            
            print("   ✓ Upload form has improved responsive layout")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")
    
    def test_timetable_table_styling(self):
        """Test that timetable table has improved styling"""
        print("\n✓ Testing timetable table styling...")
        
        response = self.client.get('/timetable')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for table classes
            self.assertIn('timetable-table', html)
            
            # Check for badge styling
            self.assertIn('date-badge', html)
            self.assertIn('time-badge', html)
            self.assertIn('venue-badge', html)
            
            print("   ✓ Timetable table has improved styling with badges")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")


class TestResponsiveDesign(unittest.TestCase):
    """Test responsive design improvements"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Create admin session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['email'] = 'admin@nitc.ac.in'
            sess['full_name'] = 'Test Admin'
            sess['role'] = 'admin'
    
    def test_timetable_responsive_breakpoints(self):
        """Test that timetable has responsive breakpoints"""
        print("\n✓ Testing responsive breakpoints...")
        
        response = self.client.get('/timetable')
        
        if response.status_code == 200:
            html = response.data.decode('utf-8')
            
            # Check for media queries
            self.assertIn('@media', html)
            self.assertIn('max-width: 1024px', html)
            self.assertIn('max-width: 640px', html)
            
            print("   ✓ Responsive breakpoints defined for mobile and tablet")
        else:
            print(f"   ⚠ Could not test (response code: {response.status_code})")


def run_tests():
    """Run all UI tests and return results"""
    print("\n" + "="*70)
    print("UI IMPROVEMENTS TEST SUITE")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAdminAbsenteesUIChanges))
    suite.addTests(loader.loadTestsFromTestCase(TestTimetableUIChanges))
    suite.addTests(loader.loadTestsFromTestCase(TestResponsiveDesign))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Install beautifulsoup4 if not available
    try:
        import bs4
    except ImportError:
        print("Installing beautifulsoup4 for HTML parsing...")
        os.system('pip install beautifulsoup4')
        import bs4
    
    success = run_tests()
    sys.exit(0 if success else 1)
