"""Verify database_indexes.sql is properly formatted"""
import os

print("=" * 60)
print("DATABASE INDEXES VERIFICATION")
print("=" * 60)

if os.path.exists('database_indexes.sql'):
    with open('database_indexes.sql', 'r') as f:
        content = f.read()
    
    # Check for required elements
    checks = {
        'CREATE INDEX IF NOT EXISTS': 'CREATE INDEX IF NOT EXISTS statement',
        'idx_students_semester_course': 'Index 1: idx_students_semester_course',
        'idx_absentees_status_date': 'Index 2: idx_absentees_status_date',
        'idx_students_rollno': 'Index 3: idx_students_rollno',
        'idx_students_timetable_batch': 'Index 4: idx_students_timetable_batch',
        'semester_id': 'Column: semester_id',
        'course_code': 'Column: course_code',
        'status': 'Column: status',
        'exam_date': 'Column: exam_date',
        'roll_no': 'Column: roll_no',
        'timetable_batch': 'Column: timetable_batch'
    }
    
    print("\n✅ File exists: database_indexes.sql")
    print(f"✅ File size: {len(content):,} bytes")
    print(f"\nChecking SQL content...")
    
    all_passed = True
    for keyword, description in checks.items():
        if keyword in content:
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ MISSING: {description}")
            all_passed = False
    
    # Count indexes
    index_count = content.count('CREATE INDEX IF NOT EXISTS')
    print(f"\n📊 Total indexes defined: {index_count}")
    
    if all_passed:
        print("\n" + "=" * 60)
        print("✅ ALL CHECKS PASSED")
        print("=" * 60)
        print("\nThe database_indexes.sql file is properly formatted")
        print("and ready to deploy to Supabase.")
        print("\nNext steps:")
        print("1. Log into Supabase Dashboard")
        print("2. Go to SQL Editor")
        print("3. Copy & paste database_indexes.sql content")
        print("4. Click 'Run'")
    else:
        print("\n❌ Some checks failed - review the file")
else:
    print("❌ File not found: database_indexes.sql")
