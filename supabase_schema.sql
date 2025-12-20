-- Supabase PostgreSQL Schema for NITC Exam Cell
-- Run this in Supabase SQL Editor before deploying

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff',
    created_at TIMESTAMP DEFAULT NOW()
);

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
    semester_id BIGINT REFERENCES semesters(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_students_semester_id ON students(semester_id);
CREATE INDEX IF NOT EXISTS idx_students_course_code ON students(course_code);
CREATE INDEX IF NOT EXISTS idx_students_roll_no ON students(roll_no);
CREATE INDEX IF NOT EXISTS idx_students_program_name ON students(program_name);
CREATE INDEX IF NOT EXISTS idx_semesters_db_name ON semesters(db_name);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE semesters ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid errors on re-run)
DROP POLICY IF EXISTS "Enable all for service role" ON users;
DROP POLICY IF EXISTS "Enable all for service role" ON semesters;
DROP POLICY IF EXISTS "Enable all for service role" ON students;

-- Create policies to allow service role to access everything
CREATE POLICY "Enable all for service role" ON users
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

COMMENT ON TABLE users IS 'Stores admin and staff user accounts';
COMMENT ON TABLE semesters IS 'Stores academic semester information';
COMMENT ON TABLE students IS 'Stores student enrollment data per semester';
COMMENT ON TABLE user_files IS 'Metadata for uploaded files in Supabase Storage';

-- ============================================
-- ABSENTEES TRACKING SYSTEM
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
    marked_by TEXT NOT NULL,  -- username of staff who marked
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by TEXT  -- admin who approved
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

COMMENT ON TABLE absentees IS 'Stores absent student records marked by staff for admin consolidation';
