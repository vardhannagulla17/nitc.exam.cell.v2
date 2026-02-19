import sqlite3
import os
import time
from flask import current_app

# Simple in-memory cache for dashboard stats
_stats_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 600  # Cache for 10 minutes (600 seconds) - balance between freshness and performance
}

def get_db_connection(db_path=None):
    """Get database connection"""
    if db_path is None:
        db_path = current_app.config['DATABASE_PATH']
    
    # Ensure absolute path
    if not os.path.isabs(db_path):
        db_path = os.path.join(current_app.config['BASE_DIR'], db_path)
    
    return sqlite3.connect(db_path)

def invalidate_stats_cache():
    """Invalidate the stats cache to force refresh on next request"""
    global _stats_cache
    _stats_cache['data'] = None
    _stats_cache['timestamp'] = 0
    print("Stats cache invalidated")

def get_semester_stats(force_refresh=False):
    """Calculate actual statistics from the database with caching
    
    Args:
        force_refresh: If True, bypass cache and recalculate stats
    """
    global _stats_cache
    
    # Check if we have valid cached data
    current_time = time.time()
    cache_age = current_time - _stats_cache['timestamp']
    
    if not force_refresh and _stats_cache['data'] is not None and cache_age < _stats_cache['ttl']:
        print(f"Using cached stats (age: {cache_age:.1f}s)")
        return _stats_cache['data']
    
    # Cache miss or expired - recalculate
    print("Recalculating stats (cache miss or expired)")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all semester databases
        cursor.execute('SELECT db_name FROM semesters')
        semester_dbs = cursor.fetchall()
        
        # Filter out entries whose DB files no longer exist and clean them up
        existing_semester_dbs = []
        missing_db_names = []
        for (db_name,) in semester_dbs:
            abs_db_path = db_name if os.path.isabs(db_name) else os.path.join(current_app.config['BASE_DIR'], db_name)
            if db_name and os.path.exists(abs_db_path):
                existing_semester_dbs.append((db_name,))
            else:
                missing_db_names.append(db_name)
        
        if missing_db_names:
            try:
                cursor.executemany('DELETE FROM semesters WHERE db_name = ?', [(n,) for n in missing_db_names if n])
                conn.commit()
            except Exception as _cleanup_err:
                pass
        semester_dbs = existing_semester_dbs
        
        total_students = 0
        unique_courses = set()
        total_semesters = len(semester_dbs)

        # Calculate totals from each semester database
        for (db_name,) in semester_dbs:
            try:
                abs_db_path = db_name if os.path.isabs(db_name) else os.path.join(current_app.config['BASE_DIR'], db_name)
                sem_conn = sqlite3.connect(abs_db_path)
                sem_cursor = sem_conn.cursor()
                
                # Count total student records (each enrollment row)
                sem_cursor.execute('SELECT COUNT(*) FROM students')
                student_count = sem_cursor.fetchone()[0]
                total_students += student_count

                # Get unique course codes
                sem_cursor.execute('SELECT DISTINCT course_code FROM students')
                courses = sem_cursor.fetchall()
                unique_courses.update(course[0] for course in courses)

                sem_conn.close()
            except Exception as e:
                print(f"Error processing semester database {db_name}: {str(e)}")
                continue

        conn.close()
        
        stats = {
            'total_students': total_students,
            'total_courses': len(unique_courses),
            'total_semesters': total_semesters
        }
        
        # Update cache
        _stats_cache['data'] = stats
        _stats_cache['timestamp'] = time.time()
        print(f"Stats cached: {stats}")
        
        return stats
    except Exception as e:
        print(f"Error calculating semester stats: {str(e)}")
        # Don't cache errors
        return {
            'total_students': 0,
            'total_courses': 0,
            'total_semesters': 0
        }

def cleanup_semester_databases():
    """Clean up semester databases when files are deleted"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT db_name FROM semesters')
        semester_dbs = [row[0] for row in cursor.fetchall()]
        cursor.execute('DELETE FROM semesters')
        conn.commit()
        conn.close()
        
        # Remove semester-specific databases
        for db_path in semester_dbs:
            try:
                if db_path and os.path.exists(db_path):
                    os.remove(db_path)
            except Exception as remove_err:
                print(f"Warning: could not remove semester db {db_path}: {remove_err}")
        
        # Invalidate cache after cleanup
        invalidate_stats_cache()
    except Exception as cleanup_err:
        print(f"Warning: cleanup after file delete failed: {cleanup_err}")

def get_semester_db_path(db_name):
    """Get absolute path for semester database"""
    if os.path.isabs(db_name):
        return db_name
    return os.path.join(current_app.config['BASE_DIR'], db_name)
