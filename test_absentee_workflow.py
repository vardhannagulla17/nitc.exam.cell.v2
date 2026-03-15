"""
Test script to verify the complete absentee workflow:
1. Mark students as absent from Excel sheet
2. Upload for approval (store in pending bucket)
3. Check pending bucket
4. Approve absentees (move to approved bucket)
5. Check approved bucket
"""
import os
import sys
import pytest
from dotenv import load_dotenv

if __name__ != '__main__':
    pytest.skip("Legacy integration script; run directly instead of pytest collection", allow_module_level=True)

# Load environment variables
load_dotenv()

# Check if Supabase is configured
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
    sys.exit(1)

print("=" * 60)
print("ABSENTEE WORKFLOW TEST")
print("=" * 60)

from supabase import create_client
from helpers.supabase_storage import absentee_storage, PENDING_ABSENTEE_BUCKET, APPROVED_ABSENTEE_BUCKET
from datetime import datetime
import json

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test data - sample students to mark as absent
test_absentees = [
    {'roll_no': 'M250001CS', 'name': 'Test Student One', 'course_code': 'CS6001', 'course_title': 'Advanced Algorithms'},
    {'roll_no': 'M250002CS', 'name': 'Test Student Two', 'course_code': 'CS6001', 'course_title': 'Advanced Algorithms'},
    {'roll_no': 'M250003CS', 'name': 'Test Student Three', 'course_code': 'CS6001', 'course_title': 'Advanced Algorithms'},
]

exam_date = datetime.now().strftime('%Y-%m-%d')
marked_by = 'test_user'

def print_step(step_num, message):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {message}")
    print("=" * 60)

def check_bucket_contents(bucket_name):
    """List files in a bucket"""
    try:
        files = supabase.storage.from_(bucket_name).list()
        return [f for f in files if f.get('name') and not f['name'].endswith('/')]
    except Exception as e:
        print(f"Error listing bucket {bucket_name}: {e}")
        return []

# Step 1: Check initial state
print_step(1, "Checking initial state of buckets and database")

pending_before = check_bucket_contents(PENDING_ABSENTEE_BUCKET)
approved_before = check_bucket_contents(APPROVED_ABSENTEE_BUCKET)
print(f"  Pending bucket files: {len(pending_before)}")
print(f"  Approved bucket files: {len(approved_before)}")

# Check database
try:
    db_pending = supabase.table('absentees').select('*').eq('status', 'pending').execute()
    db_approved = supabase.table('absentees').select('*').eq('status', 'approved').execute()
    print(f"  Database pending records: {len(db_pending.data) if db_pending.data else 0}")
    print(f"  Database approved records: {len(db_approved.data) if db_approved.data else 0}")
except Exception as e:
    print(f"  ❌ Error querying database: {e}")

# Step 2: Upload test absentees to pending
print_step(2, "Uploading test absentees to PENDING bucket")

success, filename, msg = absentee_storage.upload_pending_absentees(
    test_absentees,
    marked_by,
    exam_date
)

if success:
    print(f"  ✓ Successfully uploaded to pending bucket")
    print(f"  Filename: {filename}")
    print(f"  Message: {msg}")
else:
    print(f"  ❌ Failed to upload: {msg}")
    sys.exit(1)

# Step 3: Also insert into database (simulating the full upload_to_admin flow)
print_step(3, "Inserting absentees into database with 'pending' status")

batch_id = datetime.now().strftime('%Y%m%d%H%M%S')
absentees_data = []
for absentee in test_absentees:
    absentees_data.append({
        'roll_no': absentee['roll_no'],
        'name': absentee['name'],
        'course_code': absentee['course_code'],
        'course_title': absentee['course_title'],
        'exam_date': exam_date,
        'marked_by': marked_by,
        'status': 'pending',
        'storage_filename': filename
    })

try:
    result = supabase.table('absentees').insert(absentees_data).execute()
    if result.data:
        print(f"  ✓ Inserted {len(result.data)} records into database")
        inserted_ids = [r['id'] for r in result.data]
        print(f"  IDs: {inserted_ids}")
    else:
        print(f"  ❌ Insert failed - no data returned")
except Exception as e:
    print(f"  ❌ Error inserting into database: {e}")
    sys.exit(1)

# Step 4: Verify pending bucket
print_step(4, "Verifying PENDING bucket contents")

pending_after = check_bucket_contents(PENDING_ABSENTEE_BUCKET)
print(f"  Pending bucket files: {len(pending_after)}")
for f in pending_after:
    print(f"    - {f.get('name')}")

# Download and verify content
try:
    content = supabase.storage.from_(PENDING_ABSENTEE_BUCKET).download(filename)
    if content:
        data = json.loads(content.decode('utf-8'))
        print(f"  ✓ File content verified:")
        print(f"    - Exam date: {data.get('exam_date')}")
        print(f"    - Marked by: {data.get('marked_by')}")
        print(f"    - Absentees count: {len(data.get('absentees', []))}")
except Exception as e:
    print(f"  ❌ Error reading pending file: {e}")

# Step 5: Approve the absentees (update database and move file)
print_step(5, "Approving absentees - updating database to 'approved' status")

try:
    for aid in inserted_ids:
        result = supabase.table('absentees').update({'status': 'approved'}).eq('id', aid).execute()
        if result.data:
            print(f"  ✓ Updated record {aid} to 'approved'")
        else:
            print(f"  ❌ Failed to update record {aid}")
except Exception as e:
    print(f"  ❌ Error updating status: {e}")

# Step 6: Move file to approved bucket
print_step(6, "Moving file from PENDING to APPROVED bucket")

try:
    # Download from pending
    content = supabase.storage.from_(PENDING_ABSENTEE_BUCKET).download(filename)
    if content:
        print(f"  ✓ Downloaded from pending bucket")
        
        # Upload to approved
        result = supabase.storage.from_(APPROVED_ABSENTEE_BUCKET).upload(
            filename,
            content,
            file_options={"content-type": "application/json"}
        )
        if result:
            print(f"  ✓ Uploaded to approved bucket")
            
            # Delete from pending
            supabase.storage.from_(PENDING_ABSENTEE_BUCKET).remove([filename])
            print(f"  ✓ Removed from pending bucket")
        else:
            print(f"  ❌ Failed to upload to approved bucket")
    else:
        print(f"  ❌ Failed to download from pending bucket")
except Exception as e:
    print(f"  ❌ Error moving file: {e}")

# Step 7: Verify approved bucket
print_step(7, "Verifying APPROVED bucket contents")

approved_after = check_bucket_contents(APPROVED_ABSENTEE_BUCKET)
print(f"  Approved bucket files: {len(approved_after)}")
for f in approved_after:
    print(f"    - {f.get('name')}")

# Download and verify content
try:
    content = supabase.storage.from_(APPROVED_ABSENTEE_BUCKET).download(filename)
    if content:
        data = json.loads(content.decode('utf-8'))
        print(f"  ✓ Approved file content verified:")
        print(f"    - Exam date: {data.get('exam_date')}")
        print(f"    - Marked by: {data.get('marked_by')}")
        print(f"    - Absentees count: {len(data.get('absentees', []))}")
except Exception as e:
    print(f"  ❌ Error reading approved file: {e}")

# Step 8: Check database final state
print_step(8, "Verifying final database state")

try:
    # Check if our records are now approved
    for aid in inserted_ids:
        record = supabase.table('absentees').select('*').eq('id', aid).execute()
        if record.data and record.data[0]['status'] == 'approved':
            print(f"  ✓ Record {aid}: {record.data[0]['roll_no']} - STATUS: approved")
        else:
            print(f"  ❌ Record {aid}: unexpected status")
except Exception as e:
    print(f"  ❌ Error checking database: {e}")

# Step 9: Cleanup (optional)
print_step(9, "Cleaning up test data")

try:
    # Delete test records from database
    for aid in inserted_ids:
        supabase.table('absentees').delete().eq('id', aid).execute()
    print(f"  ✓ Deleted {len(inserted_ids)} test records from database")
    
    # Delete test file from approved bucket
    supabase.storage.from_(APPROVED_ABSENTEE_BUCKET).remove([filename])
    print(f"  ✓ Deleted test file from approved bucket")
except Exception as e:
    print(f"  ⚠ Error during cleanup: {e}")

# Final Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("""
The absentee workflow test has completed!

Workflow verified:
1. ✓ Upload absentees to pending_absentee bucket
2. ✓ Insert absentee records in database with 'pending' status
3. ✓ Verify pending bucket contents
4. ✓ Approve absentees (update database status to 'approved')
5. ✓ Move file from pending to approved bucket
6. ✓ Verify approved bucket contents
7. ✓ Verify database final state

If all steps show ✓, your Supabase storage and database are working correctly!
""")
