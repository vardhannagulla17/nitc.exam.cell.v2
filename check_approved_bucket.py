"""Quick check of approved bucket contents"""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client
import json

s = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_ANON_KEY'])

print("=" * 50)
print("APPROVED BUCKET CONTENTS")
print("=" * 50)

files = s.storage.from_('approved_absentee').list()
approved_files = [f for f in files if f.get('name') and not f['name'].endswith('/')]

if approved_files:
    print(f"\nFound {len(approved_files)} file(s):\n")
    for f in approved_files:
        print(f"  - {f['name']}")
        # Try to read the content
        try:
            content = s.storage.from_('approved_absentee').download(f['name'])
            if content:
                data = json.loads(content.decode('utf-8'))
                print(f"    Exam Date: {data.get('exam_date')}")
                print(f"    Marked By: {data.get('marked_by')}")
                print(f"    Absentees: {len(data.get('absentees', []))}")
        except Exception as e:
            print(f"    Error reading: {e}")
else:
    print("\nNo files in approved bucket.")

print("\n" + "=" * 50)
print("PENDING BUCKET CONTENTS")
print("=" * 50)

files = s.storage.from_('pending_absentee').list()
pending_files = [f for f in files if f.get('name') and not f['name'].endswith('/')]

if pending_files:
    print(f"\nFound {len(pending_files)} file(s):\n")
    for f in pending_files:
        print(f"  - {f['name']}")
else:
    print("\nNo files in pending bucket.")
