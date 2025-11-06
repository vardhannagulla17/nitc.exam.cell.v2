import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from helpers.utils import sort_by_roll_number

from .database import get_db_connection

def init_db():
    """Initialize the database with users, semesters, and students tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            academic_year TEXT NOT NULL,
            semester_type TEXT NOT NULL,
            degree_level TEXT NOT NULL,
            exam_type TEXT NOT NULL,
            db_name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            email_id TEXT,
            student_sess TEXT,
            course_code TEXT,
            credits INTEGER,
            course_title TEXT,
            program_name TEXT,
            timetable_batch TEXT,
            slot_code TEXT,
            main_instructor TEXT,
            primary_mail TEXT,
            course_category_code TEXT,
            semester_id INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (semester_id) REFERENCES semesters (id)
        )
    ''')
    
    # Create default admin user
    default_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, role) 
        VALUES (?, ?, ?)
    ''', ('admin', default_password, 'admin'))
    
    # Create sample staff users
    staff_password = generate_password_hash('staff123')
    sample_staff = [
        ('staff1', staff_password, 'staff'),
        ('staff2', staff_password, 'staff'),
        ('staff3', staff_password, 'staff')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO users (username, password_hash, role) 
        VALUES (?, ?, ?)
    ''', sample_staff)
    
    conn.commit()
    conn.close()

def get_semester_db_name(academic_year, semester_type, sheet_type, exam_type):
    """Generate database name for semester"""
    return f"students_{academic_year.replace('-', '_')}_{semester_type}_{sheet_type}_{exam_type}.db"

def create_semester_db(db_name):
    """Create a semester-specific database"""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            email_id TEXT,
            student_sess TEXT,
            course_code TEXT,
            credits INTEGER,
            course_title TEXT,
            program_name TEXT,
            timetable_batch TEXT,
            slot_code TEXT,
            main_instructor TEXT,
            primary_mail TEXT,
            course_category_code TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    return True

def load_excel_to_db(file_source, academic_year, semester_type, sheet_type, exam_type):
    """Load Excel data into semester-specific SQLite database
    
    Args:
        file_source: Either a file path (string) or BytesIO object containing Excel data
        academic_year: Academic year string
        semester_type: Semester type (monsoon/winter)
        sheet_type: Sheet type (UG/PG/PhD/combined)
        exam_type: Exam type (midsem/endsem)
    """
    try:
        # Read Excel file - handle both file path and BytesIO object
        if hasattr(file_source, 'read'):
            # It's a file-like object (BytesIO)
            df = pd.read_excel(file_source, engine='openpyxl')
        else:
            # It's a file path string
            df = pd.read_excel(file_source, engine='openpyxl')
        
        # Filter data based on sheet type if not combined (vectorized)
        if sheet_type != 'combined':
            roll_series = df.get('RollNo')
            if roll_series is not None:
                prefixes = roll_series.astype(str).str[0].str.upper()
                level_map = {'B': 'UG', 'M': 'PG', 'P': 'PhD'}
                levels = prefixes.map(level_map)
                df = df[levels == sheet_type].copy()
            else:
                df = df.iloc[0:0].copy()
        
        # Generate database name for this semester
        db_name = get_semester_db_name(academic_year, semester_type, sheet_type, exam_type)
        
        # Create semester-specific database
        create_semester_db(db_name)
        
        # Connect to main database to record semester info
        main_conn = sqlite3.connect('exam_cell.db')
        main_cursor = main_conn.cursor()
        
        # Insert or update semester record
        main_cursor.execute('''
            INSERT OR REPLACE INTO semesters 
            (academic_year, semester_type, degree_level, exam_type, db_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (academic_year, semester_type, sheet_type, exam_type, db_name))
        
        semester_id = main_cursor.lastrowid
        main_conn.commit()
        main_conn.close()
        
        # Connect to semester-specific database
        sem_conn = sqlite3.connect(db_name)
        
        # Clear existing data for this semester
        sem_conn.execute('DELETE FROM students')
        
        # Insert new data
        for _, row in df.iterrows():
            sem_conn.execute('''
                INSERT INTO students (
                    roll_no, name, email_id, student_sess, course_code, credits,
                    course_title, program_name, timetable_batch, slot_code,
                    main_instructor, primary_mail, course_category_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(row.get('RollNo', '')),
                str(row.get('NameasPerXStd', '')),
                str(row.get('EmailId', '')),
                str(row.get('studentsess', '')),
                str(row.get('CourseCode', '')),
                int(row.get('Credits', 0)) if pd.notna(row.get('Credits')) else 0,
                str(row.get('CourseTitle', '')),
                str(row.get('ProgramName', '')),
                str(row.get('TimetableBatch', '')),
                str(row.get('SlotCode', '')),
                str(row.get('MainInstructor', '')),
                str(row.get('PrimaryMail', '')),
                str(row.get('CourseCategoryCode', ''))
            ))
        
        sem_conn.commit()
        sem_conn.close()
        
        sheet_type_display = 'All Programs' if sheet_type == 'combined' else sheet_type
        return True, f"Data loaded successfully for {academic_year} {semester_type} {sheet_type_display} {exam_type} ({len(df)} records)"
    except Exception as e:
        return False, f"Error loading data: {str(e)}"

def get_user_by_credentials(username, password):
    """Get user by username and password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, password_hash, role FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[1], password):
        return {'id': user[0], 'username': username, 'role': user[2]}
    return None

def get_semester_stats():
    """Get statistics from all semesters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM semesters')
    total_semesters = cursor.fetchone()[0]
    
    cursor.execute('SELECT db_name FROM semesters')
    semester_dbs = cursor.fetchall()
    
    total_students = 0
    total_courses = 0
    
    for (db_name,) in semester_dbs:
        try:
            sem_conn = sqlite3.connect(db_name)
            sem_cursor = sem_conn.cursor()
            
            sem_cursor.execute('SELECT COUNT(*) FROM students')
            students_count = sem_cursor.fetchone()[0]
            total_students += students_count
            
            sem_cursor.execute('SELECT COUNT(DISTINCT course_code) FROM students')
            courses_count = sem_cursor.fetchone()[0]
            total_courses += courses_count
            
            sem_conn.close()
        except sqlite3.Error:
            continue
    
    conn.close()
    
    return {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_semesters': total_semesters
    }

def get_program_level(roll_no):
    """Get program level based on roll number prefix"""
    if not roll_no:
        return None
    prefix = str(roll_no)[0].upper()
    if prefix == 'B':
        return 'UG'
    elif prefix == 'M':
        return 'PG'
    elif prefix == 'P':
        return 'PhD'
    return None

def get_semesters_for_program_level(program_level=None):
    """Get all semesters that have students from a specific program level"""
    conn = sqlite3.connect('exam_cell.db')
    cursor = conn.cursor()
    
    # Get all semesters
    cursor.execute('''
        SELECT DISTINCT s.id, s.academic_year, s.semester_type, s.degree_level, s.exam_type 
        FROM semesters s
        ORDER BY s.academic_year DESC, s.semester_type
    ''')
    semesters = cursor.fetchall()
    conn.close()
    
    if not semesters:
        return []
        
    return semesters

def get_all_semesters():
    """Get all available semesters"""
    conn = sqlite3.connect('exam_cell.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, academic_year, semester_type, degree_level, exam_type FROM semesters ORDER BY academic_year DESC, semester_type')
    semesters = cursor.fetchall()
    conn.close()
    return semesters

def get_courses_for_semester(semester_id, program_level=None):
    """Get all courses for a specific semester and program level"""
    print(f"DEBUG: get_courses_for_semester called with semester_id={semester_id}, program_level={program_level}")
    
    try:
        conn = sqlite3.connect('exam_cell.db')
        cursor = conn.cursor()
        cursor.execute('SELECT db_name, academic_year, semester_type FROM semesters WHERE id = ?', (semester_id,))
        semester_info = cursor.fetchone()
        conn.close()
        
        if not semester_info:
            print(f"DEBUG: No semester found with ID {semester_id}")
            return []
            
        print(f"DEBUG: Found semester database: {semester_info[0]}")
    
        sem_conn = sqlite3.connect(semester_info[0])
        cursor = sem_conn.cursor()
        
        # First check if we have any students
        cursor.execute('SELECT COUNT(*) FROM students')
        student_count = cursor.fetchone()[0]
        print(f"DEBUG: Found {student_count} total students in semester database")
        
        if program_level:
            # Map program level to roll number prefix
            prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
            prefix = prefix_map.get(program_level)
            
            if prefix:
                # Get courses for specific program level
                query = '''
                    SELECT DISTINCT s1.course_code, s1.course_title
                    FROM students s1
                    WHERE EXISTS (
                        SELECT 1 FROM students s2
                        WHERE s2.course_code = s1.course_code
                        AND substr(s2.roll_no, 1, 1) = ?
                    )
                    ORDER BY s1.course_code
                '''
                cursor.execute(query, (prefix,))
                courses = cursor.fetchall()
                print(f"DEBUG: Found {len(courses)} courses for program level {program_level} (prefix {prefix})")
            else:
                print(f"DEBUG: Invalid program level: {program_level}")
                courses = []
        else:
            # Get all courses
            cursor.execute('SELECT DISTINCT course_code, course_title FROM students ORDER BY course_code')
            courses = cursor.fetchall()
            print(f"DEBUG: Found {len(courses)} total courses")
        
        sem_conn.close()
        return courses
        
    except sqlite3.Error as e:
        print(f"DEBUG: Database error in get_courses_for_semester: {e}")
        return []
    except Exception as e:
        print(f"DEBUG: Unexpected error in get_courses_for_semester: {e}")
        return []