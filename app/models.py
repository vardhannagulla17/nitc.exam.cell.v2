import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from helpers.utils import sort_by_roll_number
from supabase_client import supabase

from .database import get_db_connection, USE_SUPABASE_DB

def detect_excel_column(df, possible_names):
    """Smart column detection - tries to find the best matching column name"""
    # Convert all column names to lowercase for comparison
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    # Try each possible name
    for name in possible_names:
        name_lower = name.lower()
        # Exact match
        if name_lower in df_columns_lower:
            return df_columns_lower[name_lower]
        
        # Partial match (column contains the keyword)
        for col_lower, col_original in df_columns_lower.items():
            if name_lower in col_lower or col_lower in name_lower:
                return col_original
    
    return None

def init_db():
    """Initialize the database with users, semesters, and students tables"""
    if USE_SUPABASE_DB:
        # For Supabase, tables are created via SQL Editor or migrations
        # Just ensure default users exist
        try:
            # Check if users table exists and has data
            result = supabase.table('users').select('id').limit(1).execute()
            
            # If no users, create default ones
            if not result.data:
                admin_users = [
                    {'username': 'vardhan', 'password_hash': generate_password_hash('vardhan123'), 'role': 'admin'},
                    {'username': 'pavan', 'password_hash': generate_password_hash('pavan123'), 'role': 'admin'},
                    {'username': 'abhinav', 'password_hash': generate_password_hash('abhinav123'), 'role': 'admin'},
                    {'username': 'saketh', 'password_hash': generate_password_hash('saketh123'), 'role': 'admin'},
                    {'username': 'staff', 'password_hash': generate_password_hash('staff123'), 'role': 'staff'}
                ]
                supabase.table('users').insert(admin_users).execute()
                print("✅ Created default users in Supabase")
        except Exception as e:
            print(f"⚠️ Supabase init_db error: {e}")
            print("Please create tables manually in Supabase SQL Editor:")
            print("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS semesters (
                id BIGSERIAL PRIMARY KEY,
                academic_year TEXT NOT NULL,
                semester_type TEXT NOT NULL,
                degree_level TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                db_name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS students (
                id BIGSERIAL PRIMARY KEY,
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
                semester_id BIGINT REFERENCES semesters(id),
                uploaded_at TIMESTAMP DEFAULT NOW()
            );
            """)
    else:
        # SQLite for local development
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
        
        # Create default admin users
        admin_users = [
            ('vardhan', generate_password_hash('vardhan123'), 'admin'),
            ('pavan', generate_password_hash('pavan123'), 'admin'),
            ('abhinav', generate_password_hash('abhinav123'), 'admin'),
            ('saketh', generate_password_hash('saketh123'), 'admin')
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO users (username, password_hash, role) 
            VALUES (?, ?, ?)
        ''', admin_users)
        
        # Create staff user
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, role) 
            VALUES (?, ?, ?)
        ''', ('staff', generate_password_hash('staff123'), 'staff'))
        
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
    """Load Excel data into database (Supabase PostgreSQL or SQLite)
    
    Args:
        file_source: Either a file path (string) or BytesIO object containing Excel data
        academic_year: Academic year string
        semester_type: Semester type (monsoon/winter)
        sheet_type: Sheet type (UG/PG/PhD/combined)
        exam_type: Exam type (midsem/endsem)
    """
    try:
        # Debug info
        import os
        print(f"DEBUG: VERCEL={os.environ.get('VERCEL')}, USE_SUPABASE_DB={USE_SUPABASE_DB}, supabase={'initialized' if supabase else 'None'}")
        
        # Read Excel file - handle both file path and BytesIO object
        if hasattr(file_source, 'read'):
            df = pd.read_excel(file_source, engine='openpyxl')
        else:
            df = pd.read_excel(file_source, engine='openpyxl')
        
        # Debug: Print column names
        print(f"DEBUG: Excel columns: {list(df.columns)}")
        print(f"DEBUG: First row sample: {df.head(1).to_dict('records') if len(df) > 0 else 'No data'}")
        
        # Detect column names using smart matching
        col_roll = detect_excel_column(df, ['RollNo', 'Roll No', 'Roll_No', 'ROLL NO', 'Roll Number', 'Rollno'])
        col_name = detect_excel_column(df, ['StudentName', 'Student Name', 'Name', 'STUDENT NAME', 'Student_Name', 'STUDENTNAME'])
        col_email = detect_excel_column(df, ['Email_Id', 'Email', 'EmailId', 'Email ID', 'E-mail', 'Mail'])
        col_sess = detect_excel_column(df, ['Student_Sess', 'Session', 'Student Session', 'Sess'])
        col_course_code = detect_excel_column(df, ['CourseCode', 'Course Code', 'Course_Code', 'COURSE CODE'])
        col_credits = detect_excel_column(df, ['Credits', 'Credit', 'CREDITS'])
        col_course_title = detect_excel_column(df, ['CourseTitle', 'Course Title', 'Course_Title', 'COURSE TITLE', 'Title'])
        col_program = detect_excel_column(df, ['ProgramName', 'Program Name', 'Program', 'PROGRAM NAME', 'Programme'])
        col_batch = detect_excel_column(df, ['Timetable_Batch', 'Batch', 'Time Table Batch', 'TimetableBatch'])
        col_slot = detect_excel_column(df, ['Slot_Code', 'Slot', 'Slot Code', 'SlotCode'])
        col_instructor = detect_excel_column(df, ['Main_Instructor', 'Instructor', 'Main Instructor', 'Faculty'])
        col_primary_mail = detect_excel_column(df, ['Primary_Mail', 'Primary Mail', 'PrimaryMail'])
        col_category = detect_excel_column(df, ['Course_Category_Code', 'Category', 'Course Category', 'CategoryCode'])
        
        if not col_roll:
            return False, "Error: Could not find Roll Number column in Excel file. Please ensure the file has a column for roll numbers."
        
        print(f"DEBUG: Detected columns - Roll: {col_roll}, Name: {col_name}, Course: {col_course_code}")
        
        # Filter data based on sheet type if not combined
        if sheet_type != 'combined':
            roll_series = df.get('RollNo')
            if roll_series is not None:
                prefixes = roll_series.astype(str).str[0].str.upper()
                level_map = {'B': 'UG', 'M': 'PG', 'P': 'PhD'}
                levels = prefixes.map(level_map)
                df = df[levels == sheet_type].copy()
            else:
                df = df.iloc[0:0].copy()
        
        if USE_SUPABASE_DB:
            if not supabase:
                return False, "Error: Supabase not configured. Please check SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            
            try:
                # Supabase PostgreSQL implementation
                db_name = f"{academic_year}_{semester_type}_{sheet_type}_{exam_type}"
                
                # Insert or update semester record
                semester_data = {
                    'academic_year': academic_year,
                    'semester_type': semester_type,
                    'degree_level': sheet_type,
                    'exam_type': exam_type,
                    'db_name': db_name
                }
                
                # Check if semester exists
                existing = supabase.table('semesters').select('id').eq('db_name', db_name).execute()
                if existing.data:
                    semester_id = existing.data[0]['id']
                    # Delete old students for this semester
                    supabase.table('students').delete().eq('semester_id', semester_id).execute()
                else:
                    # Create new semester
                    result = supabase.table('semesters').insert(semester_data).execute()
                    semester_id = result.data[0]['id']
            except Exception as supabase_error:
                error_msg = str(supabase_error)
                if 'relation' in error_msg.lower() and 'does not exist' in error_msg.lower():
                    return False, "Database tables not found. Please run the SQL script in Supabase SQL Editor (see supabase_schema.sql)"
                return False, f"Supabase error: {error_msg}"
            
            # Prepare student data for batch insert
            students_data = []
            for _, row in df.iterrows():
                student = {
                    'roll_no': str(row.get(col_roll, '')) if col_roll else '',
                    'name': str(row.get(col_name, '')) if col_name else '',
                    'email_id': str(row.get(col_email, '')) if col_email else '',
                    'student_sess': str(row.get(col_sess, '')) if col_sess else '',
                    'course_code': str(row.get(col_course_code, '')) if col_course_code else '',
                    'credits': int(row.get(col_credits, 0)) if col_credits and pd.notna(row.get(col_credits)) else 0,
                    'course_title': str(row.get(col_course_title, '')) if col_course_title else '',
                    'program_name': str(row.get(col_program, '')) if col_program else '',
                    'timetable_batch': str(row.get(col_batch, '')) if col_batch else '',
                    'slot_code': str(row.get(col_slot, '')) if col_slot else '',
                    'main_instructor': str(row.get(col_instructor, '')) if col_instructor else '',
                    'primary_mail': str(row.get(col_primary_mail, '')) if col_primary_mail else '',
                    'course_category_code': str(row.get(col_category, '')) if col_category else '',
                    'semester_id': semester_id
                }
                students_data.append(student)
            
            # Batch insert students (Supabase can handle 1000 rows at a time)
            batch_size = 1000
            for i in range(0, len(students_data), batch_size):
                batch = students_data[i:i+batch_size]
                supabase.table('students').insert(batch).execute()
            
            sheet_type_display = 'All Programs' if sheet_type == 'combined' else sheet_type
            return True, f"Data loaded successfully to Supabase for {academic_year} {semester_type} {sheet_type_display} {exam_type} ({len(df)} records)"
            
        else:
            # SQLite implementation (local development)
            db_name = get_semester_db_name(academic_year, semester_type, sheet_type, exam_type)
            create_semester_db(db_name)
            
            # Connect to main database to record semester info
            main_conn = sqlite3.connect('exam_cell.db')
            main_cursor = main_conn.cursor()
            
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
                    str(row.get(col_roll, '')) if col_roll else '',
                    str(row.get(col_name, '')) if col_name else '',
                    str(row.get(col_email, '')) if col_email else '',
                    str(row.get(col_sess, '')) if col_sess else '',
                    str(row.get(col_course_code, '')) if col_course_code else '',
                    int(row.get(col_credits, 0)) if col_credits and pd.notna(row.get(col_credits)) else 0,
                    str(row.get(col_course_title, '')) if col_course_title else '',
                    str(row.get(col_program, '')) if col_program else '',
                    str(row.get(col_batch, '')) if col_batch else '',
                    str(row.get(col_slot, '')) if col_slot else '',
                    str(row.get(col_instructor, '')) if col_instructor else '',
                    str(row.get(col_primary_mail, '')) if col_primary_mail else '',
                    str(row.get(col_category, '')) if col_category else ''
                ))
            
            sem_conn.commit()
            sem_conn.close()
            
            sheet_type_display = 'All Programs' if sheet_type == 'combined' else sheet_type
            return True, f"Data loaded successfully for {academic_year} {semester_type} {sheet_type_display} {exam_type} ({len(df)} records)"
    except Exception as e:
        return False, f"Error loading data: {str(e)}"
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
    if USE_SUPABASE_DB:
        try:
            result = supabase.table('users').select('id, password_hash, role').eq('username', username).execute()
            if result.data and len(result.data) > 0:
                user = result.data[0]
                if check_password_hash(user['password_hash'], password):
                    return {'id': user['id'], 'username': username, 'role': user['role']}
            return None
        except Exception as e:
            print(f"Supabase auth error: {e}")
            return None
    else:
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
    if USE_SUPABASE_DB and supabase:
        try:
            # Get all semesters from Supabase
            result = supabase.table('semesters').select('id, academic_year, semester_type, degree_level, exam_type').order('academic_year', desc=True).order('semester_type').execute()
            return [(s['id'], s['academic_year'], s['semester_type'], s['degree_level'], s['exam_type']) for s in result.data]
        except:
            return []
    else:
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
    if USE_SUPABASE_DB and supabase:
        try:
            result = supabase.table('semesters').select('id, academic_year, semester_type, degree_level, exam_type').order('academic_year', desc=True).order('semester_type').execute()
            return [(s['id'], s['academic_year'], s['semester_type'], s['degree_level'], s['exam_type']) for s in result.data]
        except:
            return []
    else:
        conn = sqlite3.connect('exam_cell.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, academic_year, semester_type, degree_level, exam_type FROM semesters ORDER BY academic_year DESC, semester_type')
        semesters = cursor.fetchall()
        conn.close()
        return semesters

def get_courses_for_semester(semester_id, program_level=None):
    """Get all courses for a specific semester and program level"""
    print(f"DEBUG: get_courses_for_semester called with semester_id={semester_id}, program_level={program_level}")
    print(f"DEBUG: USE_SUPABASE_DB={USE_SUPABASE_DB}, supabase={supabase}")
    
    try:
        if USE_SUPABASE_DB and supabase:
            # Query students directly with semester_id filter
            query = supabase.table('students').select('course_code, course_title').eq('semester_id', semester_id)
            
            if program_level:
                prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
                prefix = prefix_map.get(program_level)
                if prefix:
                    # Filter by roll number prefix using LIKE
                    query = query.like('roll_no', f'{prefix}%')
            
            result = query.execute()
            
            # Get unique courses
            courses_dict = {}
            for row in result.data:
                code = row['course_code']
                if code not in courses_dict:
                    courses_dict[code] = row['course_title']
            
            courses = sorted([(code, title) for code, title in courses_dict.items()])
            print(f"DEBUG: Found {len(courses)} courses from Supabase")
            return courses
        else:
            # SQLite implementation
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
            
            cursor.execute('SELECT COUNT(*) FROM students')
            student_count = cursor.fetchone()[0]
            print(f"DEBUG: Found {student_count} total students in semester database")
            
            if program_level:
                prefix_map = {'UG': 'B', 'PG': 'M', 'PhD': 'P'}
                prefix = prefix_map.get(program_level)
                
                if prefix:
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
                cursor.execute('SELECT DISTINCT course_code, course_title FROM students ORDER BY course_code')
                courses = cursor.fetchall()
                print(f"DEBUG: Found {len(courses)} total courses")
            
            sem_conn.close()
            return courses
        
    except Exception as e:
        print(f"DEBUG: Error in get_courses_for_semester: {e}")
        return []