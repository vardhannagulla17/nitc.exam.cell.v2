-- Supabase PostgreSQL Schema for NITC Exam Cell
-- This version is idempotent - can be run multiple times safely

-- Create users table with email-based authentication
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',
    is_approved BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by TEXT
);

-- Migration: Add new columns if they don't exist (for existing databases)
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS approved_by TEXT;

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_approved ON users(is_approved);

-- Create pending_registrations table for OTP verification
CREATE TABLE IF NOT EXISTS pending_registrations (
    email TEXT PRIMARY KEY,
    otp TEXT NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster lookups and cleanup of expired entries
CREATE INDEX IF NOT EXISTS idx_pending_registrations_expires_at ON pending_registrations(expires_at);

-- Create semesters table
CREATE TABLE IF NOT EXISTS semesters (
    id BIGSERIAL PRIMARY KEY,
    academic_year TEXT NOT NULL,
    semester_type TEXT NOT NULL,
    degree_level TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    db_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create students table
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
    section TEXT,
    semester_id BIGINT REFERENCES semesters(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Migration: Add section column if it doesn't exist (for existing databases)
ALTER TABLE students ADD COLUMN IF NOT EXISTS section TEXT;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_students_semester_id ON students(semester_id);
CREATE INDEX IF NOT EXISTS idx_students_course_code ON students(course_code);
CREATE INDEX IF NOT EXISTS idx_students_roll_no ON students(roll_no);
CREATE INDEX IF NOT EXISTS idx_students_program_name ON students(program_name);
CREATE INDEX IF NOT EXISTS idx_students_section ON students(section);
CREATE INDEX IF NOT EXISTS idx_semesters_db_name ON semesters(db_name);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_registrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE semesters ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid errors on re-run)
DROP POLICY IF EXISTS "Enable all for service role" ON users;
DROP POLICY IF EXISTS "Enable all for service role" ON pending_registrations;
DROP POLICY IF EXISTS "Enable all for service role" ON semesters;
DROP POLICY IF EXISTS "Enable all for service role" ON students;

-- Create policies to allow service role to access everything
CREATE POLICY "Enable all for service role" ON users
    FOR ALL 
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON pending_registrations
    FOR ALL 
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON semesters
    FOR ALL 
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Enable all for service role" ON students
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- Optional: Create user_files table for Supabase Storage metadata
CREATE TABLE IF NOT EXISTS user_files (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    mime TEXT,
    size BIGINT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_files for better performance
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_filename ON user_files(filename);


-- ============================================
-- ABSENTEES TRACKING SYSTEM (NEW)
-- ============================================

-- Create absentees table for staff to mark absent students
CREATE TABLE IF NOT EXISTS absentees (
    id BIGSERIAL PRIMARY KEY,
    roll_no TEXT NOT NULL,
    name TEXT NOT NULL,
    course_code TEXT NOT NULL,
    course_title TEXT,
    exam_date DATE NOT NULL,
    semester_id BIGINT REFERENCES semesters(id) ON DELETE CASCADE,
    marked_by TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by TEXT
);

-- Create indexes for absentees table
CREATE INDEX IF NOT EXISTS idx_absentees_course_code ON absentees(course_code);
CREATE INDEX IF NOT EXISTS idx_absentees_exam_date ON absentees(exam_date);
CREATE INDEX IF NOT EXISTS idx_absentees_status ON absentees(status);
CREATE INDEX IF NOT EXISTS idx_absentees_marked_by ON absentees(marked_by);
CREATE INDEX IF NOT EXISTS idx_absentees_semester_id ON absentees(semester_id);

-- Enable RLS for absentees
ALTER TABLE absentees ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if exists
DROP POLICY IF EXISTS "Enable all for service role" ON absentees;

-- Create policy for absentees
CREATE POLICY "Enable all for service role" ON absentees
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- Add new columns for storage file tracking and rejection handling
ALTER TABLE absentees ADD COLUMN IF NOT EXISTS storage_filename TEXT;
ALTER TABLE absentees ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP;
ALTER TABLE absentees ADD COLUMN IF NOT EXISTS rejected_by TEXT;

-- Create index on storage_filename for better performance
CREATE INDEX IF NOT EXISTS idx_absentees_storage_filename ON absentees(storage_filename);


-- ============================================
-- EXAM TIMETABLE SYSTEM
-- ============================================

-- Create exam_timetable table to store exam schedules
CREATE TABLE IF NOT EXISTS exam_timetable (
    id BIGSERIAL PRIMARY KEY,
    semester_id BIGINT REFERENCES semesters(id) ON DELETE CASCADE,
    course_code TEXT NOT NULL,
    course_title TEXT,
    exam_date DATE NOT NULL,
    exam_time TEXT,
    venue TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT
);

-- Create indexes for exam_timetable
CREATE INDEX IF NOT EXISTS idx_exam_timetable_semester_id ON exam_timetable(semester_id);
CREATE INDEX IF NOT EXISTS idx_exam_timetable_course_code ON exam_timetable(course_code);
CREATE INDEX IF NOT EXISTS idx_exam_timetable_exam_date ON exam_timetable(exam_date);

-- Enable RLS for exam_timetable
ALTER TABLE exam_timetable ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if exists
DROP POLICY IF EXISTS "Enable all for service role" ON exam_timetable;

-- Create policy for exam_timetable
CREATE POLICY "Enable all for service role" ON exam_timetable
    FOR ALL 
    USING (true)
    WITH CHECK (true);


-- ============================================
-- STORAGE BUCKET POLICIES
-- ============================================
-- Run these in Supabase SQL Editor to allow access to storage buckets

-- Policy for pending_absentee bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('pending_absentee', 'pending_absentee', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Allow all operations on pending_absentee" ON storage.objects
    FOR ALL USING (bucket_id = 'pending_absentee') WITH CHECK (bucket_id = 'pending_absentee');

-- Policy for approved_absentee bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('approved_absentee', 'approved_absentee', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Allow all operations on approved_absentee" ON storage.objects
    FOR ALL USING (bucket_id = 'approved_absentee') WITH CHECK (bucket_id = 'approved_absentee');

-- Policy for rejected_absentee bucket
INSERT INTO storage.buckets (id, name, public) 
VALUES ('rejected_absentee', 'rejected_absentee', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Allow all operations on rejected_absentee" ON storage.objects
    FOR ALL USING (bucket_id = 'rejected_absentee') WITH CHECK (bucket_id = 'rejected_absentee');
