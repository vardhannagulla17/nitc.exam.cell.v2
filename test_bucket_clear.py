"""
Quick test to verify bucket deletion works
"""
import os
from dotenv import load_dotenv
load_dotenv()

from helpers.supabase_storage import absentee_storage, PENDING_ABSENTEE_BUCKET

print("=" * 70)
print("TESTING BUCKET DELETION")
print("=" * 70)

# Check initial state
print("\n1. Checking current bucket contents...")
pending_files = absentee_storage.list_pending_absentees()
print(f"   Pending bucket has {len(pending_files)} files")
if pending_files:
    for f in pending_files:
        print(f"   - {f.get('name')}")

# Try to clear the bucket
print("\n2. Attempting to clear pending bucket...")
success, message, count = absentee_storage.clear_pending_bucket()

print(f"\n3. Result:")
print(f"   Success: {success}")
print(f"   Message: {message}")
print(f"   Count: {count}")

# Check final state
print("\n4. Verifying deletion...")
pending_files_after = absentee_storage.list_pending_absentees()
print(f"   Pending bucket now has {len(pending_files_after)} files")

if len(pending_files_after) == 0:
    print("\n✅ SUCCESS: Bucket cleared successfully!")
else:
    print(f"\n❌ FAILED: Bucket still has {len(pending_files_after)} files")
    for f in pending_files_after:
        print(f"   - {f.get('name')}")

print("\n" + "=" * 70)
