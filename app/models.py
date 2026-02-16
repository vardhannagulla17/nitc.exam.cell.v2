import sqlite3
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from helpers.utils import sort_by_roll_number
from supabase_client import supabase

from .database import get_db_connection, USE_SUPABASE_DB

# Valid email domain for registration
VALID_EMAIL_DOMAIN = 'nitc.ac.in'

# OTP Configuration
OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6

# Email configuration (from environment variables)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'NITC Exam Cell')

def generate_otp():
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))

def send_otp_email(email, otp, full_name):
    """Send OTP to user's email"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"⚠️ SMTP not configured. OTP for {email}: {otp}")
        return True, "OTP generated (email not configured - check console)"
    
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'NITC Exam Cell - Verify Your Email (OTP: {otp})'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_FROM or SMTP_USER}>'
        msg['To'] = email
        
        # Plain text version
        text = f"""
Hello {full_name},

Your OTP for NITC Exam Cell registration is: {otp}

This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.

If you did not request this, please ignore this email.

Regards,
NITC Exam Cell Team
"""
        
        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1e293b; margin: 0; padding: 0; background-color: #f0fdfa; }}
        .email-wrapper {{ background-color: #f0fdfa; padding: 40px 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(20, 184, 166, 0.15); }}
        .header {{ background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); color: white; padding: 40px 30px; text-align: center; }}
        .header h2 {{ margin: 0; font-size: 28px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header p {{ margin: 8px 0 0 0; font-size: 14px; opacity: 0.95; }}
        .content {{ background: #ffffff; padding: 40px 30px; }}
        .content p {{ color: #475569; margin: 12px 0; font-size: 16px; }}
        .otp-box {{ background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%); border: 3px solid #14b8a6; padding: 30px; text-align: center; margin: 30px 0; border-radius: 12px; box-shadow: 0 2px 8px rgba(20, 184, 166, 0.1); }}
        .otp {{ font-size: 42px; font-weight: bold; color: #0d9488; letter-spacing: 12px; display: block; font-family: 'Courier New', monospace; }}
        .info-text {{ background: #f0fdfa; border-left: 4px solid #14b8a6; padding: 15px; margin: 20px 0; border-radius: 4px; color: #0f766e; font-size: 14px; }}
        .footer {{ text-align: center; padding: 30px; background: #f8fafc; color: #64748b; font-size: 13px; border-top: 1px solid #e2e8f0; }}
        .footer strong {{ color: #0d9488; }}
        .highlight {{ color: #0d9488; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="container">
            <div class="header">
                <h2>🎓 NITC Exam Cell</h2>
                <p>Email Verification</p>
            </div>
            <div class="content">
                <p>Hello <strong>{full_name}</strong>,</p>
                <p>Thank you for registering with NITC Exam Cell. Please use the verification code below to complete your registration:</p>
                <div class="otp-box">
                    <span class="otp">{otp}</span>
                </div>
                <div class="info-text">
                    ⏱️ This OTP is valid for <span class="highlight">{OTP_EXPIRY_MINUTES} minutes</span> only.
                </div>
                <p>If you did not request this verification code, please ignore this email. Your account will remain secure.</p>
            </div>
            <div class="footer">
                <p><strong>National Institute of Technology Calicut</strong></p>
                <p>NIT Campus P.O., Calicut, Kerala - 673601</p>
                <p style="margin-top: 10px; font-size: 12px; color: #94a3b8;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        # Send email - try SSL first (port 465), then TLS (port 587)
        try:
            if SMTP_PORT == 465:
                # Use SSL
                import ssl
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=10) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                # Use TLS (port 587)
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
        except Exception as smtp_error:
            # If port 587 fails, try port 465 with SSL
            print(f"⚠️ Port {SMTP_PORT} failed, trying port 465 with SSL...")
            import ssl
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        
        print(f"✅ OTP email sent to {email}")
        return True, "OTP sent successfully to your email"
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        # In debug mode, still allow registration with OTP shown in message
        DEBUG_MODE = os.environ.get('DEBUG_OTP', 'true').lower() == 'true'
        if DEBUG_MODE:
            return True, f"Email failed but DEBUG mode active. Your OTP is: {otp}"
        return False, f"Failed to send OTP email: {str(e)}"

def create_pending_registration(email, full_name, password):
    """Create a pending registration with OTP - stored in database"""
    otp = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    email_lower = email.lower()
    password_hash = generate_password_hash(password)
    
    try:
        if USE_SUPABASE_DB and supabase:
            # Delete any existing pending registration for this email
            supabase.table('pending_registrations').delete().eq('email', email_lower).execute()
            
            # Insert new pending registration
            supabase.table('pending_registrations').insert({
                'email': email_lower,
                'otp': otp,
                'full_name': full_name,
                'password_hash': password_hash,
                'expires_at': expires_at.isoformat()
            }).execute()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Delete any existing pending registration for this email
            cursor.execute('DELETE FROM pending_registrations WHERE email = ?', (email_lower,))
            
            # Insert new pending registration
            cursor.execute('''
                INSERT INTO pending_registrations (email, otp, full_name, password_hash, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (email_lower, otp, full_name, password_hash, expires_at))
            
            conn.commit()
            conn.close()
        
        # Send OTP email
        success, message = send_otp_email(email, otp, full_name)
        return success, message, otp
    except Exception as e:
        print(f"Error creating pending registration: {e}")
        return False, f"Registration failed: {str(e)}", None

def verify_otp_and_register(email, otp):
    """Verify OTP and complete registration - reads from database"""
    email_lower = email.lower()
    
    try:
        # Get pending registration from database
        if USE_SUPABASE_DB and supabase:
            result = supabase.table('pending_registrations').select('*').eq('email', email_lower).execute()
            if not result.data:
                return False, "No pending registration found for this email. Please register again."
            registration = result.data[0]
            expires_at = datetime.fromisoformat(registration['expires_at'].replace('Z', '+00:00'))
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pending_registrations WHERE email = ?', (email_lower,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return False, "No pending registration found for this email. Please register again."
            
            registration = {
                'email': row[0],
                'otp': row[1],
                'full_name': row[2],
                'password_hash': row[3],
                'expires_at': row[4]
            }
            expires_at = datetime.fromisoformat(registration['expires_at'])
        
        # Check if OTP expired
        if datetime.now() > expires_at:
            # Delete expired registration
            if USE_SUPABASE_DB and supabase:
                supabase.table('pending_registrations').delete().eq('email', email_lower).execute()
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM pending_registrations WHERE email = ?', (email_lower,))
                conn.commit()
                conn.close()
            return False, "OTP has expired. Please register again."
        
        # Check if OTP matches
        if registration['otp'] != otp:
            return False, "Invalid OTP. Please check and try again."
        
        # OTP verified - create user account (auto-approved)
        if USE_SUPABASE_DB and supabase:
            # Check if email already exists
            existing = supabase.table('users').select('id').eq('email', email_lower).execute()
            if existing.data:
                supabase.table('pending_registrations').delete().eq('email', email_lower).execute()
                return False, "An account with this email already exists."
            
            # Create user (auto-approved since email is verified)
            user_data = {
                'email': email_lower,
                'full_name': registration['full_name'],
                'password_hash': registration['password_hash'],
                'role': 'staff',
                'is_approved': True,
                'is_active': True,
                'approved_at': datetime.now().isoformat()
            }
            supabase.table('users').insert(user_data).execute()
            
            # Delete pending registration
            supabase.table('pending_registrations').delete().eq('email', email_lower).execute()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email_lower,))
            if cursor.fetchone():
                cursor.execute('DELETE FROM pending_registrations WHERE email = ?', (email_lower,))
                conn.commit()
                conn.close()
                return False, "An account with this email already exists."
            
            # Create user (auto-approved since email is verified)
            cursor.execute('''
                INSERT INTO users (email, full_name, password_hash, role, is_approved, is_active, approved_at)
                VALUES (?, ?, ?, 'staff', 1, 1, ?)
            ''', (email_lower, registration['full_name'], registration['password_hash'], datetime.now()))
            
            # Delete pending registration
            cursor.execute('DELETE FROM pending_registrations WHERE email = ?', (email_lower,))
            
            conn.commit()
            conn.close()
        
        return True, "Registration successful! You can now login."
    
    except Exception as e:
        print(f"Error verifying OTP and registering: {e}")
        return False, f"Registration failed: {str(e)}"

def resend_otp(email):
    """Resend OTP for pending registration - updates database"""
    email_lower = email.lower()
    
    try:
        # Check if pending registration exists
        if USE_SUPABASE_DB and supabase:
            result = supabase.table('pending_registrations').select('full_name').eq('email', email_lower).execute()
            if not result.data:
                return False, "No pending registration found. Please register again."
            full_name = result.data[0]['full_name']
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT full_name FROM pending_registrations WHERE email = ?', (email_lower,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return False, "No pending registration found. Please register again."
            full_name = row[0]
        
        # Generate new OTP
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        # Update OTP in database
        if USE_SUPABASE_DB and supabase:
            supabase.table('pending_registrations').update({
                'otp': otp,
                'expires_at': expires_at.isoformat()
            }).eq('email', email_lower).execute()
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE pending_registrations SET otp = ?, expires_at = ? WHERE email = ?',
                         (otp, expires_at, email_lower))
            conn.commit()
            conn.close()
        
        # Send new OTP
        success, message = send_otp_email(email, otp, full_name)
        return success, message
    
    except Exception as e:
        print(f"Error resending OTP: {e}")
        return False, f"Failed to resend OTP: {str(e)}"

def validate_email_domain(email):
    """Validate that email ends with @nitc.ac.in"""
    if not email:
        return False
    return email.lower().endswith(f'@{VALID_EMAIL_DOMAIN}')

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
        # Just ensure default admin users exist
        try:
            # Check if users table exists and has data
            result = supabase.table('users').select('id').limit(1).execute()
            
            # If no users, create default admin users
            if not result.data:
                admin_users = [
                    {'email': 'vardhan@nitc.ac.in', 'full_name': 'Vardhan', 'password_hash': generate_password_hash('vardhan123'), 'role': 'admin', 'is_approved': True, 'is_active': True},
                    {'email': 'pavan@nitc.ac.in', 'full_name': 'Pavan', 'password_hash': generate_password_hash('pavan123'), 'role': 'admin', 'is_approved': True, 'is_active': True},
                    {'email': 'abhinav@nitc.ac.in', 'full_name': 'Abhinav', 'password_hash': generate_password_hash('abhinav123'), 'role': 'admin', 'is_approved': True, 'is_active': True},
                    {'email': 'saketh@nitc.ac.in', 'full_name': 'Saketh', 'password_hash': generate_password_hash('saketh123'), 'role': 'admin', 'is_approved': True, 'is_active': True}
                ]
                supabase.table('users').insert(admin_users).execute()
                print("✅ Created default admin users in Supabase")
        except Exception as e:
            print(f"⚠️ Supabase init_db error: {e}")
            print("Please create tables manually in Supabase SQL Editor using supabase_schema.sql")
    else:
        # SQLite for local development
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table with email-based authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                is_approved BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by TEXT
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
        
        # Create pending_registrations table for OTP verification
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_registrations (
                email TEXT PRIMARY KEY,
                otp TEXT NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default admin users (pre-approved)
        admin_users = [
            ('vardhan@nitc.ac.in', 'Vardhan', generate_password_hash('vardhan123'), 'admin', 1, 1),
            ('pavan@nitc.ac.in', 'Pavan', generate_password_hash('pavan123'), 'admin', 1, 1),
            ('abhinav@nitc.ac.in', 'Abhinav', generate_password_hash('abhinav123'), 'admin', 1, 1),
            ('saketh@nitc.ac.in', 'Saketh', generate_password_hash('saketh123'), 'admin', 1, 1)
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO users (email, full_name, password_hash, role, is_approved, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', admin_users)
        
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
        col_name = detect_excel_column(df, ['NameasPerXstd', 'StudentName', 'Student Name', 'Name', 'STUDENT NAME', 'Student_Name', 'STUDENTNAME', 'NameAsPerXStd'])
        col_email = detect_excel_column(df, ['EmailId', 'Email_Id', 'Email', 'Email ID', 'E-mail', 'Mail'])
        col_sess = detect_excel_column(df, ['studentSess', 'Student_Sess', 'Session', 'Student Session', 'Sess', 'StudentSess'])
        col_course_code = detect_excel_column(df, ['CourseCode', 'Course Code', 'Course_Code', 'COURSE CODE'])
        col_credits = detect_excel_column(df, ['Credits', 'Credit', 'CREDITS'])
        col_course_title = detect_excel_column(df, ['CourseTitle', 'Course Title', 'Course_Title', 'COURSE TITLE', 'Title'])
        col_program = detect_excel_column(df, ['ProgramName', 'Program Name', 'Program', 'PROGRAM NAME', 'Programme'])
        col_batch = detect_excel_column(df, ['SectionBatchName', 'Section Batch Name', 'Timetable_Batch', 'Batch', 'Time Table Batch', 'TimetableBatch'])
        col_slot = detect_excel_column(df, ['Slot_Code', 'Slot', 'Slot Code', 'SlotCode'])
        col_instructor = detect_excel_column(df, ['Main_Instructor', 'Instructor', 'Main Instructor', 'Faculty'])
        col_primary_mail = detect_excel_column(df, ['Primary_Mail', 'Primary Mail', 'PrimaryMail'])
        col_category = detect_excel_column(df, ['Course_Category_Code', 'Category', 'Course Category', 'CategoryCode'])
        
        if not col_roll:
            return False, "Error: Could not find Roll Number column in Excel file. Please ensure the file has a column for roll numbers."
        
        print(f"DEBUG: Detected columns - Roll: {col_roll}, Name: {col_name}, Course: {col_course_code}")
        
        # Filter data based on sheet type if not combined
        if sheet_type != 'combined':
            if col_roll and col_roll in df.columns:
                roll_series = df[col_roll]
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

def get_user_by_credentials(email, password):
    """Get user by email and password (email-based login)"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                print("Supabase client not initialized")
                return None
            result = supabase.table('users').select('id, email, full_name, password_hash, role, is_approved, is_active').eq('email', email.lower()).execute()
            if result.data and len(result.data) > 0:
                user = result.data[0]
                if check_password_hash(user['password_hash'], password):
                    # Check if user is approved and active
                    if not user.get('is_approved', False):
                        return {'error': 'pending_approval'}
                    if not user.get('is_active', True):
                        return {'error': 'account_disabled'}
                    return {'id': user['id'], 'email': user['email'], 'full_name': user['full_name'], 'role': user['role']}
            return None
        except Exception as e:
            print(f"Supabase auth error: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, password_hash, role, is_approved, is_active FROM users WHERE email = ?', (email.lower(),))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            # Check if user is approved and active
            if not user[4]:  # is_approved
                return {'error': 'pending_approval'}
            if not user[5]:  # is_active
                return {'error': 'account_disabled'}
            return {'id': user[0], 'email': email.lower(), 'full_name': user[1], 'role': user[3]}
        return None

def register_user(email, full_name, password):
    """Register a new user (staff) with email validation"""
    email = email.lower().strip()
    full_name = full_name.strip()
    
    # Validate email domain
    if not validate_email_domain(email):
        return False, f"Only @{VALID_EMAIL_DOMAIN} email addresses are allowed"
    
    # Check if email already exists
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            
            result = supabase.table('users').select('id').eq('email', email).execute()
            if result.data:
                return False, "An account with this email already exists"
            
            # Create new user (not approved by default)
            new_user = {
                'email': email,
                'full_name': full_name,
                'password_hash': generate_password_hash(password),
                'role': 'staff',
                'is_approved': False,
                'is_active': True
            }
            supabase.table('users').insert(new_user).execute()
            return True, "Registration successful! Please wait for admin approval."
        except Exception as e:
            print(f"Registration error: {e}")
            return False, f"Registration failed: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return False, "An account with this email already exists"
        
        try:
            cursor.execute('''
                INSERT INTO users (email, full_name, password_hash, role, is_approved, is_active)
                VALUES (?, ?, ?, 'staff', 0, 1)
            ''', (email, full_name, generate_password_hash(password)))
            conn.commit()
            conn.close()
            return True, "Registration successful! Please wait for admin approval."
        except Exception as e:
            conn.close()
            return False, f"Registration failed: {str(e)}"

def get_all_users():
    """Get all users for admin management"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return []
            result = supabase.table('users').select('id, email, full_name, role, is_approved, is_active, created_at, approved_at, approved_by').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, full_name, role, is_approved, is_active, created_at, approved_at, approved_by FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return [{'id': u[0], 'email': u[1], 'full_name': u[2], 'role': u[3], 'is_approved': bool(u[4]), 'is_active': bool(u[5]), 'created_at': u[6], 'approved_at': u[7], 'approved_by': u[8]} for u in users]

def get_pending_users():
    """Get users pending approval"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return []
            result = supabase.table('users').select('id, email, full_name, role, created_at').eq('is_approved', False).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Error getting pending users: {e}")
            return []
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, full_name, role, created_at FROM users WHERE is_approved = 0 ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return [{'id': u[0], 'email': u[1], 'full_name': u[2], 'role': u[3], 'created_at': u[4]} for u in users]

def approve_user(user_id, approved_by):
    """Approve a user registration"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            supabase.table('users').update({
                'is_approved': True,
                'approved_at': datetime.now().isoformat(),
                'approved_by': approved_by
            }).eq('id', user_id).execute()
            return True, "User approved successfully"
        except Exception as e:
            return False, f"Failed to approve user: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET is_approved = 1, approved_at = ?, approved_by = ? WHERE id = ?
            ''', (datetime.now().isoformat(), approved_by, user_id))
            conn.commit()
            conn.close()
            return True, "User approved successfully"
        except Exception as e:
            conn.close()
            return False, f"Failed to approve user: {str(e)}"

def reject_user(user_id):
    """Reject/delete a user registration"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            supabase.table('users').delete().eq('id', user_id).execute()
            return True, "User registration rejected"
        except Exception as e:
            return False, f"Failed to reject user: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True, "User registration rejected"
        except Exception as e:
            conn.close()
            return False, f"Failed to reject user: {str(e)}"

def toggle_user_active(user_id):
    """Toggle user active status"""
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            # Get current status
            result = supabase.table('users').select('is_active').eq('id', user_id).execute()
            if not result.data:
                return False, "User not found"
            current_status = result.data[0]['is_active']
            new_status = not current_status
            supabase.table('users').update({'is_active': new_status}).eq('id', user_id).execute()
            return True, f"User {'activated' if new_status else 'deactivated'} successfully"
        except Exception as e:
            return False, f"Failed to update user: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT is_active FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False, "User not found"
            new_status = 0 if result[0] else 1
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
            conn.commit()
            conn.close()
            return True, f"User {'activated' if new_status else 'deactivated'} successfully"
        except Exception as e:
            conn.close()
            return False, f"Failed to update user: {str(e)}"

def update_user_role(user_id, new_role):
    """Update user role (admin/staff)"""
    if new_role not in ['admin', 'staff']:
        return False, "Invalid role"
    
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            supabase.table('users').update({'role': new_role}).eq('id', user_id).execute()
            return True, f"User role updated to {new_role}"
        except Exception as e:
            return False, f"Failed to update role: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
            conn.commit()
            conn.close()
            return True, f"User role updated to {new_role}"
        except Exception as e:
            conn.close()
            return False, f"Failed to update role: {str(e)}"

def delete_user(user_id, current_user_id):
    """Delete a user (cannot delete self)"""
    if str(user_id) == str(current_user_id):
        return False, "You cannot delete your own account"
    
    if USE_SUPABASE_DB:
        try:
            if not supabase:
                return False, "Database not available"
            supabase.table('users').delete().eq('id', user_id).execute()
            return True, "User deleted successfully"
        except Exception as e:
            return False, f"Failed to delete user: {str(e)}"
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True, "User deleted successfully"
        except Exception as e:
            conn.close()
            return False, f"Failed to delete user: {str(e)}"

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

# ============================================
# EXAM TIMETABLE FUNCTIONS
# ============================================

def parse_pdf_timetable(file_source):
    """Parse exam timetable from PDF file in NITC format"""
    import re
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, "PyMuPDF not installed. Please run: pip install pymupdf"
    
    try:
        # Open PDF
        if isinstance(file_source, str):
            doc = fitz.open(file_source)
        else:
            # Read from file-like object
            pdf_bytes = file_source.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Extract text from all pages
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # Parse course entries
        # Date pattern: DD-MM-YYYY or YYYY-MM-DD
        date_pattern = r'(\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})'
        # Time pattern: HH:MM – HH:MM or HH:MM-HH:MM or HH:MM − HH:MM
        time_pattern = r'(\d{1,2}:\d{2}\s*[–\-−]\s*\d{1,2}:\d{2})'
        # Course code pattern: 2-3 letters followed by 4 digits and optional letter (e.g., ME1211E, MA2013E)
        course_code_pattern = r'\b([A-Z]{2,3}\d{4}[A-Z]?)\b'
        
        # Find all course codes with their context
        entries = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for course code
            code_match = re.search(course_code_pattern, line)
            if code_match:
                course_code = code_match.group(1)
                
                # Look for date and time in nearby lines (current and next few lines)
                context = ' '.join(lines[i:min(i+5, len(lines))])
                
                date_match = re.search(date_pattern, context)
                time_match = re.search(time_pattern, context)
                
                if date_match:
                    exam_date = date_match.group(1)
                    # Convert DD-MM-YYYY to YYYY-MM-DD if needed
                    if re.match(r'\d{2}-\d{2}-\d{4}', exam_date):
                        parts = exam_date.split('-')
                        exam_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    
                    exam_time = time_match.group(1) if time_match else ''
                    # Clean up time format
                    exam_time = exam_time.replace('−', '-').replace('–', '-')
                    
                    # Try to extract course title (text after course code until date)
                    title_search = line[code_match.end():].strip()
                    # Get text before the date
                    if date_match:
                        title_candidate = context[code_match.end():context.find(date_match.group(1))].strip()
                        if len(title_candidate) > 3 and len(title_candidate) < 100:
                            title_search = title_candidate
                    
                    # Clean up title
                    title_search = re.sub(r'\s+', ' ', title_search)
                    title_search = re.sub(date_pattern, '', title_search)
                    title_search = re.sub(time_pattern, '', title_search).strip()
                    
                    # Look for venue (common NITC venues)
                    venue = ''
                    venue_pattern = r'(ECLC\s*[A-Z]|NLHC\s*\d+|MB\s*\d+|DB\s*\d+|AB\s*\d+)'
                    venue_match = re.search(venue_pattern, context, re.IGNORECASE)
                    if venue_match:
                        venue = venue_match.group(1)
                    
                    entries.append({
                        'course_code': course_code,
                        'course_title': title_search[:255] if title_search else '',
                        'exam_date': exam_date,
                        'exam_time': exam_time,
                        'venue': venue
                    })
        
        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_entries = []
        for entry in entries:
            if entry['course_code'] not in seen:
                seen.add(entry['course_code'])
                unique_entries.append(entry)
        
        return unique_entries, None
    except Exception as e:
        return None, f"Error parsing PDF: {str(e)}"

def upload_exam_timetable(file_source, semester_id, created_by, file_type='excel'):
    """Upload exam timetable from Excel or PDF file"""
    try:
        records_to_insert = []
        
        # Handle PDF files
        if file_type == 'pdf':
            entries, error = parse_pdf_timetable(file_source)
            if error:
                return False, error
            if not entries:
                return False, "No exam entries found in the PDF file. Please check the format."
            
            for entry in entries:
                records_to_insert.append({
                    'course_code': entry['course_code'],
                    'course_title': entry.get('course_title', ''),
                    'exam_date': entry['exam_date'],
                    'exam_time': entry.get('exam_time', ''),
                    'venue': entry.get('venue', '')
                })
        else:
            # Handle Excel files
            if isinstance(file_source, str):
                df = pd.read_excel(file_source)
            else:
                df = pd.read_excel(file_source)
            
            # Expected columns: Course Code, Course Title, Exam Date, Exam Time, Venue
            course_code_col = detect_excel_column(df, ['course_code', 'coursecode', 'code', 'subject_code', 'subjectcode'])
            course_title_col = detect_excel_column(df, ['course_title', 'coursetitle', 'title', 'course_name', 'coursename', 'subject', 'subject_name'])
            exam_date_col = detect_excel_column(df, ['exam_date', 'examdate', 'date', 'exam date'])
            exam_time_col = detect_excel_column(df, ['exam_time', 'examtime', 'time', 'exam time', 'timing'])
            venue_col = detect_excel_column(df, ['venue', 'room', 'hall', 'location', 'exam_venue'])
            
            if not course_code_col:
                return False, "Could not find 'Course Code' column in the Excel file"
            if not exam_date_col:
                return False, "Could not find 'Exam Date' column in the Excel file"
            
            for _, row in df.iterrows():
                course_code = str(row.get(course_code_col, '')).strip()
                if not course_code:
                    continue
                
                exam_date = row.get(exam_date_col)
                if pd.isna(exam_date):
                    continue
                
                if isinstance(exam_date, pd.Timestamp):
                    exam_date_str = exam_date.strftime('%Y-%m-%d')
                else:
                    exam_date_str = str(exam_date)[:10]
                
                records_to_insert.append({
                    'course_code': course_code,
                    'course_title': str(row.get(course_title_col, '')) if course_title_col else '',
                    'exam_date': exam_date_str,
                    'exam_time': str(row.get(exam_time_col, '')) if exam_time_col else '',
                    'venue': str(row.get(venue_col, '')) if venue_col else ''
                })
        
        if not records_to_insert:
            return False, "No valid records found in the file"
        
        records_added = 0
        
        if USE_SUPABASE_DB and supabase:
            # Clear existing timetable for this semester
            supabase.table('exam_timetable').delete().eq('semester_id', semester_id).execute()
            
            # Insert new records
            for record in records_to_insert:
                timetable_entry = {
                    'semester_id': int(semester_id),
                    'course_code': record['course_code'],
                    'course_title': record.get('course_title', ''),
                    'exam_date': record['exam_date'],
                    'exam_time': record.get('exam_time', ''),
                    'venue': record.get('venue', ''),
                    'created_by': created_by
                }
                
                supabase.table('exam_timetable').insert(timetable_entry).execute()
                records_added += 1
        else:
            # SQLite implementation
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exam_timetable (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    semester_id INTEGER,
                    course_code TEXT NOT NULL,
                    course_title TEXT,
                    exam_date DATE NOT NULL,
                    exam_time TEXT,
                    venue TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (semester_id) REFERENCES semesters (id)
                )
            ''')
            
            # Clear existing timetable for this semester
            cursor.execute('DELETE FROM exam_timetable WHERE semester_id = ?', (semester_id,))
            
            # Insert new records
            for record in records_to_insert:
                cursor.execute('''
                    INSERT INTO exam_timetable (semester_id, course_code, course_title, exam_date, exam_time, venue, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    semester_id,
                    record['course_code'],
                    record.get('course_title', ''),
                    record['exam_date'],
                    record.get('exam_time', ''),
                    record.get('venue', ''),
                    created_by
                ))
                records_added += 1
            
            conn.commit()
            conn.close()
        
        return True, f"Exam timetable uploaded successfully! {records_added} courses scheduled."
    except Exception as e:
        print(f"Error uploading timetable: {e}")
        return False, f"Error uploading timetable: {str(e)}"

def get_exam_date_for_course(course_code, semester_id):
    """Get exam date for a specific course from the timetable"""
    if USE_SUPABASE_DB and supabase:
        try:
            result = supabase.table('exam_timetable').select('exam_date, exam_time, venue').eq('semester_id', semester_id).eq('course_code', course_code).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"Error getting exam date: {e}")
            return None
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT exam_date, exam_time, venue FROM exam_timetable 
                WHERE semester_id = ? AND course_code = ?
            ''', (semester_id, course_code))
            result = cursor.fetchone()
            conn.close()
            if result:
                return {'exam_date': result[0], 'exam_time': result[1], 'venue': result[2]}
            return None
        except:
            conn.close()
            return None

def get_timetable_for_semester(semester_id):
    """Get all timetable entries for a semester"""
    if USE_SUPABASE_DB and supabase:
        try:
            result = supabase.table('exam_timetable').select('*').eq('semester_id', semester_id).order('exam_date').execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting timetable: {e}")
            return []
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT id, course_code, course_title, exam_date, exam_time, venue 
                FROM exam_timetable WHERE semester_id = ? ORDER BY exam_date
            ''', (semester_id,))
            results = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'course_code': r[1], 'course_title': r[2], 'exam_date': r[3], 'exam_time': r[4], 'venue': r[5]} for r in results]
        except:
            conn.close()
            return []

def get_courses_with_exam_dates(semester_id, program_level=None):
    """Get courses with their exam dates for a semester"""
    courses = get_courses_for_semester(semester_id, program_level)
    
    # Fetch exam dates for each course
    courses_with_dates = []
    for course in courses:
        course_code = course[0] if isinstance(course, tuple) else course.get('course_code')
        course_title = course[1] if isinstance(course, tuple) else course.get('course_title')
        
        exam_info = get_exam_date_for_course(course_code, semester_id)
        
        courses_with_dates.append({
            'course_code': course_code,
            'course_title': course_title,
            'exam_date': exam_info.get('exam_date') if exam_info else None,
            'exam_time': exam_info.get('exam_time') if exam_info else None,
            'venue': exam_info.get('venue') if exam_info else None
        })
    
    return courses_with_dates

def has_timetable_for_semester(semester_id):
    """Check if a timetable exists for the semester"""
    if USE_SUPABASE_DB and supabase:
        try:
            result = supabase.table('exam_timetable').select('id').eq('semester_id', semester_id).limit(1).execute()
            return len(result.data) > 0 if result.data else False
        except:
            return False
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT id FROM exam_timetable WHERE semester_id = ? LIMIT 1', (semester_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except:
            conn.close()
            return False