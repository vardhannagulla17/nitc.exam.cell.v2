-- Migration: Add section column to students table
-- Run this in Supabase SQL Editor

-- Add section column if it doesn't exist
ALTER TABLE students ADD COLUMN IF NOT EXISTS section TEXT;

-- Create index for section filtering
CREATE INDEX IF NOT EXISTS idx_students_section ON students(section);

-- Optional: Update existing records to extract section from roll_no or timetable_batch
-- This is a placeholder - adjust based on your data format
-- Example: If section is part of roll_no like "B210001ME" where "ME" might indicate section
-- You can run: UPDATE students SET section = substring(timetable_batch from 1 for 4) WHERE section IS NULL;

COMMENT ON COLUMN students.section IS 'Student section/batch identifier (e.g., ME01, EC02, etc.)';
