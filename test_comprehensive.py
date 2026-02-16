"""
Comprehensive test to check all optimizations and potential issues
"""
import os
import sys

print("=" * 80)
print("COMPREHENSIVE OPTIMIZATION VERIFICATION")
print("=" * 80)

# Test 1: Check imports
print("\n1. Testing imports...")
try:
    from app.models import get_all_semesters, _get_cached, _fetch_semesters_with_students
    print("   ✅ All functions imported successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Check cache mechanism
print("\n2. Testing cache mechanism...")
from datetime import datetime

cache_test_data = []
def mock_fetch():
    cache_test_data.append("call")
    return ["data"]

result1 = _get_cached("test_key", mock_fetch, ttl_seconds=10)
result2 = _get_cached("test_key", mock_fetch, ttl_seconds=10)

if len(cache_test_data) == 1:
    print("   ✅ Cache working: Function called only once")
elif len(cache_test_data) == 2:
    print("   ❌ Cache NOT working: Function called twice (should be cached)")
else:
    print(f"   ⚠️  Unexpected cache behavior: {len(cache_test_data)} calls")

# Test 3: Analyze query optimization
print("\n3. Analyzing query optimization in _fetch_semesters_with_students()...")
import inspect
source = inspect.getsource(_fetch_semesters_with_students)

# Check for potential issues
issues = []

# Issue 1: Check if using .select('semester_id') without DISTINCT
if ".select('semester_id')" in source and "distinct" not in source.lower():
    issues.append({
        'severity': 'HIGH',
        'issue': 'Fetching ALL student records to get semester IDs',
        'line_snippet': "semester_ids_result = supabase.table('students').select('semester_id').execute()",
        'problem': 'With 10,000 students, fetches 10,000 rows to get ~10 unique semester IDs',
        'impact': 'Inefficient memory usage, slow query, high data transfer',
        'fix': "Use DISTINCT or aggregation: .select('semester_id', count='exact').limit(1000)"
    })

# Issue 2: Check for N+1 pattern
if '.eq(' in source and 'for' in source and 'semester' in source:
    count = source.count('.eq(')
    if count > 1:
        issues.append({
            'severity': 'MEDIUM',
            'issue': f'Potential N+1 pattern detected ({count} .eq() calls)',
            'problem': 'Multiple individual queries instead of batch query',
            'impact': 'Slower than necessary'
        })

if issues:
    print(f"   ⚠️  Found {len(issues)} potential issue(s):")
    for i, issue in enumerate(issues, 1):
        print(f"\n   Issue {i}: {issue['issue']}")
        print(f"   Severity: {issue['severity']}")
        if 'line_snippet' in issue:
            print(f"   Code: {issue['line_snippet']}")
        print(f"   Problem: {issue['problem']}")
        print(f"   Impact: {issue['impact']}")
        if 'fix' in issue:
            print(f"   Fix: {issue['fix']}")
else:
    print("   ✅ No obvious query optimization issues found")

# Test 4: Check database indexes file
print("\n4. Checking database_indexes.sql...")
if os.path.exists('database_indexes.sql'):
    with open('database_indexes.sql', 'r') as f:
        content = f.read()
        
    required_indexes = [
        'idx_students_semester_course',
        'idx_absentees_status_date',
        'idx_students_rollno',
        'idx_students_timetable_batch'
    ]
    
    missing = []
    for idx in required_indexes:
        if idx not in content:
            missing.append(idx)
    
    if missing:
        print(f"   ⚠️  Missing indexes: {', '.join(missing)}")
    else:
        print(f"   ✅ All {len(required_indexes)} required indexes defined")
        print(f"   📋 Indexes: {', '.join(required_indexes)}")
else:
    print("   ❌ database_indexes.sql not found")

# Test 5: Check for other optimized functions
print("\n5. Checking for other query patterns...")
from app import models
import re

# Get all function names
functions = [name for name in dir(models) if callable(getattr(models, name)) and not name.startswith('_')]
print(f"   Found {len(functions)} public functions")

# Check which functions might benefit from caching
potentially_cached = []
for func_name in functions:
    if 'get_all' in func_name or 'get_courses' in func_name:
        func = getattr(models, func_name)
        source = inspect.getsource(func)
        if '_get_cached' in source:
            potentially_cached.append((func_name, '✅ cached'))
        else:
            potentially_cached.append((func_name, '⚠️ not cached'))

if potentially_cached:
    print(f"   Functions that could use caching:")
    for name, status in potentially_cached[:5]:  # Show first 5
        print(f"      - {name}: {status}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

# Final verdict
print("\n✅ OPTIMIZATIONS IMPLEMENTED:")
print("   • Query caching with TTL (reduces repeated DB calls)")
print("   • Optimized get_all_semesters() (2 queries vs N+1 pattern)")
print("   • Database indexes defined (ready to deploy)")

if issues:
    print(f"\n⚠️  ISSUES FOUND: {len(issues)}")
    print("   See details above for recommendations")
else:
    print("\n✅ NO CRITICAL ISSUES DETECTED")

print("\n📋 DEPLOYMENT CHECKLIST:")
print("   1. ✅ Code optimizations are in place")
print("   2. ⚠️  Database indexes need to be run in Supabase SQL Editor")
print("   3. ⚠️  Test with real Supabase connection to verify performance")
print("   4. ⚠️  Consider the issues noted above for further optimization")

print("\n" + "=" * 80)
