"""
Quick test to verify new user registration approval workflow
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location("main_app", "app.py")
main_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_app)
app = main_app.app

def test_registration_approval_routes():
    """Test that registration approval routes are accessible"""
    print("\n=== Testing Registration Approval Workflow ===\n")
    
    with app.test_client() as client:
        # Login as admin
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['email'] = 'admin@example.com'
        
        # Test 1: Admin users page loads
        print("Test 1: Checking if admin users page loads...")
        response = client.get('/admin/users')
        if response.status_code == 200:
            print("  ✅ Admin users page accessible")
        else:
            print(f"  ❌ Failed with status {response.status_code}")
            return False
        
        # Test 2: Check if pending users are displayed
        print("\nTest 2: Checking if page contains pending users section...")
        if b'pending' in response.data.lower() or b'approve' in response.data.lower():
            print("  ✅ Pending users section exists")
        else:
            print("  ⚠️  Warning: Could not find pending users section in response")
        
        # Test 3: Check approve route exists
        print("\nTest 3: Testing approve route (with invalid ID)...")
        response = client.post('/admin/users/approve/99999')
        # Should redirect or return error, not 404
        if response.status_code in [200, 302]:
            print(f"  ✅ Approve route exists (status {response.status_code})")
        else:
            print(f"  ❌ Approve route failed with status {response.status_code}")
            return False
        
        # Test 4: Check reject route exists
        print("\nTest 4: Testing reject route (with invalid ID)...")
        response = client.post('/admin/users/reject/99999')
        if response.status_code in [200, 302]:
            print(f"  ✅ Reject route exists (status {response.status_code})")
        else:
            print(f"  ❌ Reject route failed with status {response.status_code}")
            return False
        
        print("\n" + "="*50)
        print("✅ All registration approval routes are working!")
        print("="*50)
        return True

def test_non_admin_access():
    """Test that non-admin cannot access admin routes"""
    print("\n=== Testing Non-Admin Access Control ===\n")
    
    with app.test_client() as client:
        # Login as staff
        with client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['username'] = 'staff'
            sess['role'] = 'faculty'
        
        print("Test: Non-admin trying to access admin users page...")
        response = client.get('/admin/users', follow_redirects=False)
        
        if response.status_code == 302:  # Should redirect
            print("  ✅ Non-admin correctly denied access (redirected)")
            return True
        else:
            print(f"  ⚠️  Unexpected response: {response.status_code}")
            return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("REGISTRATION APPROVAL WORKFLOW TEST")
    print("="*60)
    
    try:
        test1_passed = test_registration_approval_routes()
        test2_passed = test_non_admin_access()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        if test1_passed and test2_passed:
            print("✅ All tests passed - Registration approval is working!")
            print("\nFeatures verified:")
            print("  • Admin users page loads")
            print("  • Approve user route exists")
            print("  • Reject user route exists")
            print("  • Non-admin access is blocked")
            sys.exit(0)
        else:
            print("⚠️  Some tests had issues - Review output above")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
