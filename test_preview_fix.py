"""Test the preview absentees fix"""
import requests
import pytest

BASE_URL = "http://127.0.0.1:5000"

def test_preview():
    try:
        requests.get(f"{BASE_URL}/", timeout=1)
    except requests.exceptions.RequestException:
        pytest.skip(f"Local server not running at {BASE_URL}")

    # Create a session to maintain login
    session = requests.Session()
    
    # First, login as admin
    print("Step 1: Logging in as admin...")
    login_response = session.post(f"{BASE_URL}/login", data={
        'username': 'admin',
        'password': 'admin123'
    }, allow_redirects=True)
    
    if 'dashboard' in login_response.url or login_response.status_code == 200:
        print("  ✓ Login successful")
    else:
        print(f"  ✗ Login may have failed - URL: {login_response.url}")
        print(f"    Response: {login_response.text[:500]}")
        return
    
    # Test 1: Preview with NO date (should show ALL approved absentees)
    print("\nStep 2: Testing preview without date (should show all approved)...")
    preview_response = session.post(f"{BASE_URL}/admin/absentees", data={
        'action': 'preview_consolidated',
        'exam_date': ''  # No date = show all
    })
    
    if 'Consolidated Absentee List' in preview_response.text:
        print("  ✓ Preview works! Found 'Consolidated Absentee List' in response")
        # Check if the absentee is shown
        if 'B251174ME' in preview_response.text:
            print("  ✓ Found the approved absentee B251174ME in the preview!")
        else:
            print("  ? Did not find B251174ME - checking content...")
            print(f"    Preview content length: {len(preview_response.text)}")
    elif 'No Approved Absentees Found' in preview_response.text:
        print("  ✗ Preview shows 'No Approved Absentees Found'")
        print(f"    Full response: {preview_response.text[:800]}")
    else:
        print(f"  ? Unknown response")
        print(f"    Response (first 800 chars): {preview_response.text[:800]}")
    
    # Test 2: Preview with specific date (2026-01-19 - the date of the approved absentee)
    print("\nStep 3: Testing preview with correct date 2026-01-19...")
    preview_response2 = session.post(f"{BASE_URL}/admin/absentees", data={
        'action': 'preview_consolidated',
        'exam_date': '2026-01-19'
    })
    
    if 'Consolidated Absentee List' in preview_response2.text:
        print("  ✓ Preview with date works!")
        if 'B251174ME' in preview_response2.text:
            print("  ✓ Found the approved absentee B251174ME!")
        else:
            print("  ? Absentee not found in preview")
    elif 'No Approved Absentees Found' in preview_response2.text:
        print("  ✗ Preview shows 'No Approved Absentees'")
    else:
        print(f"  ? Unknown response: {preview_response2.text[:500]}")
    
    # Test 3: Preview with wrong date (should show no absentees)
    print("\nStep 4: Testing preview with wrong date 2026-01-28 (today)...")
    preview_response3 = session.post(f"{BASE_URL}/admin/absentees", data={
        'action': 'preview_consolidated',
        'exam_date': '2026-01-28'
    })
    
    if 'No Approved Absentees Found' in preview_response3.text:
        print("  ✓ Correctly shows 'No Approved Absentees' for wrong date")
    elif 'Consolidated Absentee List' in preview_response3.text:
        print("  ? Found absentees even with wrong date - checking...")
        if 'B251174ME' in preview_response3.text:
            print("    (This should not happen - absentee is for 2026-01-19)")
    else:
        print(f"  ? Unknown response: {preview_response3.text[:500]}")

    print("\n✓ All tests completed!")

if __name__ == '__main__':
    test_preview()
