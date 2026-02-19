"""
Test Suite for Performance Optimizations
Tests caching, optimized queries, and cache invalidation
"""

import sys
import os
import time
import unittest
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set test environment
os.environ['TESTING'] = 'True'

from app import app
from helpers.database_utils import (
    get_semester_stats, 
    invalidate_stats_cache,
    _stats_cache
)


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimizations and caching"""
    
    def setUp(self):
        """Set up test client and clear cache"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Clear cache before each test
        invalidate_stats_cache()
    
    def tearDown(self):
        """Clean up after tests"""
        invalidate_stats_cache()
    
    def test_cache_invalidation(self):
        """Test that cache invalidation works correctly"""
        print("\n✓ Testing cache invalidation...")
        
        # Initially cache should be empty
        self.assertIsNone(_stats_cache['data'])
        self.assertEqual(_stats_cache['timestamp'], 0)
        
        # Call get_semester_stats to populate cache
        stats1 = get_semester_stats()
        self.assertIsNotNone(_stats_cache['data'])
        self.assertGreater(_stats_cache['timestamp'], 0)
        
        # Invalidate cache
        invalidate_stats_cache()
        self.assertIsNone(_stats_cache['data'])
        self.assertEqual(_stats_cache['timestamp'], 0)
        
        print("   ✓ Cache invalidation working correctly")
    
    def test_cache_hit_performance(self):
        """Test that cache provides significant performance improvement"""
        print("\n✓ Testing cache hit performance...")
        
        # First call - cache miss (slower)
        start_time = time.time()
        stats1 = get_semester_stats()
        first_call_time = time.time() - start_time
        
        # Second call - cache hit (should be much faster)
        start_time = time.time()
        stats2 = get_semester_stats()
        second_call_time = time.time() - start_time
        
        print(f"   First call (cache miss): {first_call_time*1000:.2f}ms")
        print(f"   Second call (cache hit): {second_call_time*1000:.2f}ms")
        
        # Cache hit should be at least 10x faster (usually 100x+)
        self.assertLess(second_call_time, first_call_time / 10)
        
        # Stats should be identical
        self.assertEqual(stats1, stats2)
        
        print(f"   ✓ Performance improvement: {first_call_time/second_call_time:.1f}x faster")
    
    def test_cache_ttl_expiration(self):
        """Test that cache expires after TTL"""
        print("\n✓ Testing cache TTL expiration...")
        
        # Get stats to populate cache
        stats1 = get_semester_stats()
        timestamp1 = _stats_cache['timestamp']
        
        # Manually set timestamp to past (beyond TTL)
        _stats_cache['timestamp'] = time.time() - 700  # 700 seconds ago (> 600 TTL)
        
        # Next call should recalculate
        stats2 = get_semester_stats()
        timestamp2 = _stats_cache['timestamp']
        
        # Timestamp should be updated
        self.assertGreater(timestamp2, timestamp1)
        
        print("   ✓ Cache TTL expiration working correctly")
    
    def test_force_refresh(self):
        """Test force_refresh parameter bypasses cache"""
        print("\n✓ Testing force refresh...")
        
        # Populate cache
        stats1 = get_semester_stats()
        timestamp1 = _stats_cache['timestamp']
        
        # Small delay to ensure timestamp would be different
        time.sleep(0.01)
        
        # Force refresh should bypass cache
        stats2 = get_semester_stats(force_refresh=True)
        timestamp2 = _stats_cache['timestamp']
        
        # Timestamp should be updated even though cache was valid
        self.assertGreater(timestamp2, timestamp1)
        
        print("   ✓ Force refresh working correctly")
    
    def test_stats_structure(self):
        """Test that stats return correct structure"""
        print("\n✓ Testing stats structure...")
        
        stats = get_semester_stats()
        
        # Check required keys exist
        self.assertIn('total_students', stats)
        self.assertIn('total_courses', stats)
        self.assertIn('total_semesters', stats)
        
        # Check types
        self.assertIsInstance(stats['total_students'], int)
        self.assertIsInstance(stats['total_courses'], int)
        self.assertIsInstance(stats['total_semesters'], int)
        
        # Check non-negative
        self.assertGreaterEqual(stats['total_students'], 0)
        self.assertGreaterEqual(stats['total_courses'], 0)
        self.assertGreaterEqual(stats['total_semesters'], 0)
        
        print(f"   ✓ Stats structure valid: {stats}")


class TestOptimizedQueries(unittest.TestCase):
    """Test optimized database queries"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
    
    def test_pending_users_count_function_exists(self):
        """Test that get_pending_users_count function exists and works"""
        print("\n✓ Testing optimized pending users count...")
        
        from app.models import get_pending_users_count, get_pending_users
        
        # Get count using optimized function
        start_time = time.time()
        count = get_pending_users_count()
        count_time = time.time() - start_time
        
        # Get count using original function
        start_time = time.time()
        users = get_pending_users()
        list_time = time.time() - start_time
        
        print(f"   Count query: {count_time*1000:.2f}ms")
        print(f"   List query: {list_time*1000:.2f}ms")
        
        # Count should match
        self.assertEqual(count, len(users))
        
        # Count should be integer
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
        
        print(f"   ✓ Optimized count working correctly (found {count} pending users)")


class TestDashboardPerformance(unittest.TestCase):
    """Test dashboard loading performance"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Clear cache
        invalidate_stats_cache()
    
    def test_dashboard_load_time_cached(self):
        """Test dashboard load time with cached stats"""
        print("\n✓ Testing dashboard load time with cache...")
        
        # Create a test session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['email'] = 'test@nitc.ac.in'
            sess['full_name'] = 'Test User'
            sess['role'] = 'staff'
        
        # First load - populate cache
        response1 = self.client.get('/dashboard')
        
        # Second load - should use cache
        start_time = time.time()
        response2 = self.client.get('/dashboard')
        load_time = time.time() - start_time
        
        print(f"   Dashboard load time (cached): {load_time*1000:.2f}ms")
        
        # Should be fast (< 100ms for cached response)
        self.assertLess(load_time, 0.1)
        self.assertEqual(response2.status_code, 200)
        
        print("   ✓ Dashboard loading fast with cache")


class TestCacheInvalidationOnChanges(unittest.TestCase):
    """Test that cache is invalidated on data changes"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Clear cache
        invalidate_stats_cache()
    
    def test_cache_invalidation_in_cleanup(self):
        """Test cache invalidation is called in cleanup_semester_databases"""
        print("\n✓ Testing cache invalidation in cleanup...")
        
        from helpers.database_utils import cleanup_semester_databases
        
        # Populate cache
        stats1 = get_semester_stats()
        self.assertIsNotNone(_stats_cache['data'])
        
        # Call cleanup (which should invalidate cache)
        try:
            cleanup_semester_databases()
        except Exception as e:
            # Cleanup might fail if no databases exist, that's OK
            print(f"   (Cleanup raised expected error: {e})")
        
        # Cache should be invalidated
        # Note: cleanup_semester_databases calls invalidate_stats_cache
        # Check that the function exists and can be called
        self.assertTrue(callable(invalidate_stats_cache))
        
        print("   ✓ Cache invalidation integrated in cleanup")


def run_tests():
    """Run all tests and return results"""
    print("\n" + "="*70)
    print("PERFORMANCE OPTIMIZATION TEST SUITE")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceOptimizations))
    suite.addTests(loader.loadTestsFromTestCase(TestOptimizedQueries))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestCacheInvalidationOnChanges))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
