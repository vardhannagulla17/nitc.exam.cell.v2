import os
from pathlib import Path
from supabase_client import supabase

# Check if we should use Supabase PostgreSQL or SQLite
# Use Supabase if client is available (regardless of environment)
USE_SUPABASE_DB = supabase is not None

def get_db_connection(db_name=None):
    """Get a database connection - Supabase PostgreSQL on Vercel, SQLite locally"""
    if USE_SUPABASE_DB:
        # Return Supabase client for PostgreSQL operations
        return supabase
    else:
        # Use SQLite for local development
        import sqlite3
        if not db_name:
            db_name = 'exam_cell.db'
        db_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = str(db_dir / db_name)
        return sqlite3.connect(db_path)

def execute_query(query, params=None, fetch=False, db_name=None):
    """Execute a query on either Supabase or SQLite"""
    if USE_SUPABASE_DB:
        # Supabase uses different query syntax - this needs table-specific handling
        # Will be implemented per-table in models.py
        raise NotImplementedError("Use table-specific Supabase methods")
    else:
        import sqlite3
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            last_id = cursor.lastrowid
            conn.close()
            return last_id