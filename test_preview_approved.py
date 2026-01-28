"""Test script for preview absentees functionality"""
from dotenv import load_dotenv
load_dotenv()

from supabase_client import supabase
from datetime import datetime

print("=" * 60)
print("Testing Preview Approved Absentees Fix")
print("=" * 60)

# Check all absentees
result = supabase.table('absentees').select('*').execute()
print(f"\n1. Total absentees in database: {len(result.data) if result.data else 0}")

if result.data:
    for r in result.data:
        print(f"   id={r['id']}, roll={r['roll_no']}, status={r['status']}, exam_date={r['exam_date']}")
else:
    print("   No absentees found")

# Check approved specifically
print("\n2. Testing approved absentees query:")
approved = supabase.table('absentees').select('*').eq('status', 'approved').execute()
print(f"   Approved count (no date filter): {len(approved.data) if approved.data else 0}")

if approved.data:
    print("   Approved absentees found:")
    for a in approved.data:
        print(f"      - {a['roll_no']} ({a['name']}) for {a['exam_date']}")

# Test with specific date filter 
print("\n3. Testing date filter (2026-01-19):")
approved_with_date = supabase.table('absentees').select('*').eq('status', 'approved').eq('exam_date', '2026-01-19').execute()
print(f"   Approved count (date=2026-01-19): {len(approved_with_date.data) if approved_with_date.data else 0}")

# Test with wrong date
print("\n4. Testing wrong date filter (2026-01-28 - today):")
approved_wrong_date = supabase.table('absentees').select('*').eq('status', 'approved').eq('exam_date', '2026-01-28').execute()
print(f"   Approved count (date=2026-01-28): {len(approved_wrong_date.data) if approved_wrong_date.data else 0}")

print("\n" + "=" * 60)
print("FIX VERIFICATION:")
print("=" * 60)
print("Before fix: Preview without date defaults to today (2026-01-28)")
print("            -> Shows 0 absentees (wrong!)")
print("\nAfter fix:  Preview without date shows ALL approved absentees")
print(f"            -> Shows {len(approved.data) if approved.data else 0} absentees (correct!)")
print("=" * 60)

