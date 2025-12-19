import requests
from requests.cookies import RequestsCookieJar

# Test absentee preview functionality
base_url = "http://127.0.0.1:5000"

# Create a session to maintain cookies
session = requests.Session()

# 1. Login first
print("1. Testing login...")
login_data = {
    'username': 'saketh',
    'password': 'saketh123'
}
response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
print(f"   Login status: {response.status_code}")
if response.status_code == 302:
    print("   ✓ Login successful (redirected)")
else:
    print("   ✗ Login failed")
    exit(1)

# 2. Access absentee page
print("\n2. Accessing absentee page...")
response = session.get(f"{base_url}/absentee")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print("   ✓ Absentee page loaded")
else:
    print("   ✗ Could not access absentee page")
    exit(1)

# 3. Add a test absentee to session
print("\n3. Adding test student to absentee list...")
add_data = {
    'action': 'add_absentee',
    'roll_no': 'B210001ME',
    'name': 'Test Student',
    'course_code': 'TEST101',
    'course_title': 'Test Course'
}
response = session.post(f"{base_url}/absentee", data=add_data)
print(f"   Status: {response.status_code}")
if 'Added' in response.text or response.status_code == 200:
    print("   ✓ Student added")
else:
    print("   ✗ Failed to add student")

# 4. Test preview
print("\n4. Testing preview functionality...")
preview_data = {
    'action': 'preview_absentees',
    'exam_date': '2025-12-14'
}
response = session.post(f"{base_url}/absentee", data=preview_data)
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.headers.get('Content-Type', 'Not set')}")
print(f"   Content length: {len(response.text)} bytes")

# Check if it's HTML
if 'text/html' in response.headers.get('Content-Type', ''):
    if 'National Institute of Technology Calicut' in response.text:
        if 'Absentee List' in response.text:
            if 'Test Student' in response.text:
                print("   ✓✓✓ PREVIEW WORKING PERFECTLY!")
                print("   - Correct content type (HTML)")
                print("   - Contains header")
                print("   - Contains absentee list")
                print("   - Contains test student")
            else:
                print("   ✗ Student name not found in preview")
        else:
            print("   ✗ 'Absentee List' title not found")
    else:
        print("   ✗ NITC header not found")
        print(f"   First 500 chars: {response.text[:500]}")
else:
    print("   ✗ Wrong content type - not HTML!")
    print(f"   Response preview: {response.text[:200]}")

print("\n" + "="*50)
print("Test completed!")
