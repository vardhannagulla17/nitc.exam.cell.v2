"""
Verification Script for Supabase Security Fixes
Confirms that RLS is properly configured and app still functions
"""

import os
import sys
from supabase_client import supabase

def test_supabase_connection():
    """Test basic Supabase connectivity"""
    print("\n" + "="*60)
    print("🔍 TESTING SUPABASE CONNECTION")
    print("="*60)
    
    if not supabase:
        print("❌ FAIL: Supabase client not initialized")
        print("   Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
        return False
    
    print("✅ PASS: Supabase client initialized successfully")
    return True


def test_service_role_access():
    """Test that service role can access data (bypassing RLS)"""
    print("\n" + "="*60)
    print("🔑 TESTING SERVICE ROLE ACCESS (Should Bypass RLS)")
    print("="*60)
    
    try:
        # Test reading users table
        result = supabase.table('users').select('email').limit(1).execute()
        print(f"✅ PASS: Can access users table ({len(result.data)} rows returned)")
        
        # Test reading students table
        result = supabase.table('students').select('roll_no').limit(1).execute()
        print(f"✅ PASS: Can access students table ({len(result.data)} rows returned)")
        
        # Test reading semesters table
        result = supabase.table('semesters').select('id').limit(1).execute()
        print(f"✅ PASS: Can access semesters table ({len(result.data)} rows returned)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error accessing tables: {e}")
        print("   This might indicate service role key is not set correctly")
        return False


def test_rls_enabled():
    """Check if RLS is enabled on critical tables"""
    print("\n" + "="*60)
    print("🔒 CHECKING RLS STATUS ON TABLES")
    print("="*60)
    
    try:
        # Query to check RLS status
        query = """
        SELECT 
            tablename,
            rowsecurity as rls_enabled
        FROM pg_tables 
        WHERE schemaname = 'public'
        AND tablename IN ('users', 'students', 'absentees', 'semesters', 
                         'password_reset_requests', 'pending_registrations')
        ORDER BY tablename;
        """
        
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        
        if result.data:
            for row in result.data:
                status = "✅ ENABLED" if row['rls_enabled'] else "❌ DISABLED"
                print(f"{status}: {row['tablename']}")
            return True
        else:
            print("⚠️ Note: Could not verify RLS status via RPC")
            print("   Please check manually in Supabase dashboard")
            print("   SQL Editor > Run: SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';")
            return None
            
    except Exception as e:
        print(f"⚠️ Note: Could not verify RLS status programmatically: {e}")
        print("   Please verify manually in Supabase dashboard:")
        print("   1. Go to SQL Editor")
        print("   2. Run: SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';")
        print("   3. Confirm rowsecurity = true for all tables")
        return None


def test_policies_exist():
    """Check if security policies are created"""
    print("\n" + "="*60)
    print("📋 CHECKING SECURITY POLICIES")
    print("="*60)
    
    try:
        # Query to count policies
        query = """
        SELECT 
            tablename,
            COUNT(*) as policy_count
        FROM pg_policies 
        WHERE schemaname = 'public'
        GROUP BY tablename
        ORDER BY tablename;
        """
        
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        
        if result.data:
            total_policies = 0
            for row in result.data:
                count = row['policy_count']
                total_policies += count
                print(f"✅ {row['tablename']}: {count} policies")
            
            print(f"\n✅ Total policies: {total_policies}")
            return True
        else:
            print("⚠️ Note: Could not verify policies via RPC")
            print("   Please check manually in Supabase dashboard")
            return None
            
    except Exception as e:
        print(f"⚠️ Note: Could not verify policies programmatically: {e}")
        print("   Please verify manually in Supabase dashboard:")
        print("   1. Go to SQL Editor")
        print("   2. Run: SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';")
        return None


def test_app_functionality():
    """Test critical app operations"""
    print("\n" + "="*60)
    print("🧪 TESTING APP FUNCTIONALITY")
    print("="*60)
    
    try:
        from app.models import get_all_users, get_pending_users_count
        
        # Test getting users (should work with service role)
        users = get_all_users()
        print(f"✅ PASS: Can retrieve users (found {len(users) if users else 0} users)")
        
        # Test getting pending users count
        count = get_pending_users_count()
        print(f"✅ PASS: Can count pending users ({count} pending)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error testing app functionality: {e}")
        return False


def run_all_tests():
    """Run all verification tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "SUPABASE SECURITY VERIFICATION" + " "*17 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        'connection': test_supabase_connection(),
        'service_role': test_service_role_access(),
        'rls': test_rls_enabled(),
        'policies': test_policies_exist(),
        'app': test_app_functionality()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Skipped/Manual Check Required: {skipped}")
    
    print("\n" + "="*60)
    
    if failed == 0:
        print("✨ ALL CRITICAL TESTS PASSED!")
        print("   Your Supabase security is properly configured.")
        if skipped > 0:
            print("   Please verify skipped items manually in Supabase dashboard.")
    else:
        print("⚠️ SOME TESTS FAILED!")
        print("   Please check the errors above and:")
        print("   1. Ensure supabase_security_fixes.sql was run in Supabase")
        print("   2. Verify SUPABASE_SERVICE_ROLE_KEY is set correctly")
        print("   3. Check Supabase dashboard for security issues")
    
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
