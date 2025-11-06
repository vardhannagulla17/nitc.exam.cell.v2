import os
import sqlite3
from pathlib import Path

def get_db_path(db_name=None):
    """Get the appropriate database path based on environment"""
    IS_VERCEL = bool(os.environ.get('VERCEL', False))
    
    if not db_name:
        db_name = 'exam_cell.db'
    
    if IS_VERCEL:
        # Use /tmp directory in Vercel
        db_dir = Path('/tmp')
    else:
        # Use current directory in local development
        db_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return str(db_dir / db_name)

def get_db_connection(db_name=None):
    """Get a database connection with proper path handling"""
    db_path = get_db_path(db_name)
    return sqlite3.connect(db_path)