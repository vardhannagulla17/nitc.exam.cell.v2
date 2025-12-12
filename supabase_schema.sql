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

-- Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE semesters ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role to access everything
-- These policies allow the backend to perform all operations
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

-- Insert default admin users (passwords are hashed in the application)
-- These will be created by the init_db() function in the app
-- No need to insert here - the app will handle it

COMMENT ON TABLE users IS 'Stores admin and staff user accounts';
COMMENT ON TABLE semesters IS 'Stores academic semester information';
COMMENT ON TABLE students IS 'Stores student enrollment data per semester';
