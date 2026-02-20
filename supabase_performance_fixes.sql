-- ================================================================
-- SUPABASE PERFORMANCE FIXES
-- ================================================================
-- Run this script to fix performance issues detected in Supabase
-- ================================================================

-- ================================================================
-- FIX 1: Remove Duplicate Index on students.roll_no
-- ================================================================
-- Issue: Table `public.students` has identical indexes
--        - idx_students_roll_no (from supabase_schema.sql)
--        - idx_students_rollno (from database_indexes.sql)
-- Solution: Drop one of them to save storage and improve write performance
-- ================================================================

-- Check which indexes exist on students table (for verification)
DO $$
BEGIN
    RAISE NOTICE 'Current indexes on students table:';
END $$;

SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'students'
AND schemaname = 'public'
AND indexname LIKE '%roll%'
ORDER BY indexname;

-- Drop the duplicate index (keep idx_students_rollno from database_indexes.sql)
DROP INDEX IF EXISTS public.idx_students_roll_no;

-- Verify idx_students_rollno exists (this is the one we're keeping)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'students' 
        AND indexname = 'idx_students_rollno'
    ) THEN
        RAISE NOTICE '✅ Kept index: idx_students_rollno';
    ELSE
        RAISE NOTICE '⚠️ Warning: idx_students_rollno does not exist. Creating it now...';
        CREATE INDEX idx_students_rollno ON students(roll_no);
        RAISE NOTICE '✅ Created index: idx_students_rollno';
    END IF;
END $$;

-- ================================================================
-- VERIFICATION: Check for remaining duplicate indexes
-- ================================================================
-- This query will show all indexes on the students table
-- Look for multiple indexes on roll_no column

SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename = 'students'
ORDER BY indexname;

-- Check specifically for roll_no indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename = 'students'
AND indexdef LIKE '%roll_no%'
ORDER BY indexname;

-- ================================================================
-- EXPECTED RESULT:
-- ================================================================
-- Before: 
--   - students.roll_no has 2 indexes (idx_students_roll_no, idx_students_rollno)
--   - Performance warning in Supabase dashboard
--
-- After:  
--   - students.roll_no has 1 index (idx_students_rollno)
--   - Performance warning resolved
--   - Faster insert/update operations on students table
--   - Reduced storage usage
-- ================================================================

-- Show final index status
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes 
WHERE tablename = 'students'
AND schemaname = 'public'
ORDER BY indexname;

-- ================================================================
-- NOTES:
-- ================================================================
-- 1. Duplicate indexes waste storage (2x the space)
-- 2. They slow down INSERT/UPDATE operations (must update both)
-- 3. They provide no performance benefit for SELECT queries
-- 4. We keep idx_students_rollno because it's properly named in database_indexes.sql
-- 5. This fix is safe - both indexes were identical, just different names
-- ================================================================
