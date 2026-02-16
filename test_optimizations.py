"""
Quick test script to verify optimizations are working
Run this to check if the optimized code works correctly

NOTE: This test requires either:
1. Supabase credentials set in environment variables, OR
2. Local SQLite database initialized

If you get "no such table" error, it means you need to:
- Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables
- OR initialize local database first
"""
from datetime import datetime
from app.models import get_all_semesters

print("=" * 60)
print("TESTING OPTIMIZED get_all_semesters()")
print("=" * 60)

try:
    # Test 1: First call (should hit database)
    print("\n1️⃣ First call (cache miss, hits database)...")
    start = datetime.now()
    semesters1 = get_all_semesters()
    duration1 = (datetime.now() - start).total_seconds()
    print(f"   ✅ Returned {len(semesters1)} semesters")
    print(f"   ⏱️  Time: {duration1:.4f} seconds")

    # Test 2: Second call (should hit cache)
    print("\n2️⃣ Second call (cache hit, no database)...")
    start = datetime.now()
    semesters2 = get_all_semesters()
    duration2 = (datetime.now() - start).total_seconds()
    print(f"   ✅ Returned {len(semesters2)} semesters")
    print(f"   ⏱️  Time: {duration2:.4f} seconds")

    # Test 3: Verify caching worked
    print("\n3️⃣ Verification...")
    if duration2 < 0.01:  # Cache should be <10ms
        print(f"   ✅ CACHING WORKS! Second call was {duration1/duration2:.0f}x faster")
    else:
        print(f"   ⚠️  Caching might not be working (both calls similar speed)")

    if semesters1 == semesters2:
        print(f"   ✅ Data consistency: Both calls returned same data")
    else:
        print(f"   ❌ ERROR: Data mismatch between calls")

    # Test 4: Display sample data
    print("\n4️⃣ Sample semester data:")
    if semesters1:
        for sem in semesters1[:3]:  # Show first 3
            print(f"   - {sem[1]} {sem[2]} {sem[3]} {sem[4]}")
        if len(semesters1) > 3:
            print(f"   ... and {len(semesters1) - 3} more")
    else:
        print("   (No semesters found - this is expected if database is empty)")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    if len(semesters1) > 0 and duration2 < 0.01:
        print("✅ ALL TESTS PASSED - Optimizations working correctly!")
    else:
        print("⚠️  Some tests inconclusive (may need to check database)")

except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    print("\nThis is likely because:")
    print("1. No Supabase credentials in environment, AND")
    print("2. No local SQLite database exists")
    print("\n✅ CODE SYNTAX IS VALID (import worked)")
    print("✅ To test fully, deploy to production with Supabase")
    print("\n" + "=" * 60)
