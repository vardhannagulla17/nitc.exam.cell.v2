-- ================================================================
-- SUPABASE SECURITY FIXES - Row Level Security (RLS)
-- ================================================================
-- Run this script in Supabase SQL Editor to fix all security issues
-- This will enable RLS and create proper policies for all tables
-- ================================================================

-- 1. ENABLE RLS ON ALL TABLES
-- ================================================================

-- Enable RLS on password_reset_requests
ALTER TABLE public.password_reset_requests ENABLE ROW LEVEL SECURITY;

-- Enable RLS on user_files (if exists)
ALTER TABLE IF EXISTS public.user_files ENABLE ROW LEVEL SECURITY;

-- Enable RLS on absentees
ALTER TABLE public.absentees ENABLE ROW LEVEL SECURITY;

-- Enable RLS on pending_registrations
ALTER TABLE public.pending_registrations ENABLE ROW LEVEL SECURITY;

-- Enable RLS on semesters
ALTER TABLE public.semesters ENABLE ROW LEVEL SECURITY;

-- Enable RLS on users (critical!)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Enable RLS on students
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;

-- Note: Timetables table doesn't exist - skipping RLS enable
-- ALTER TABLE IF EXISTS public.timetables ENABLE ROW LEVEL SECURITY;


-- 2. DROP EXISTING OVERLY PERMISSIVE POLICIES
-- ================================================================

-- Drop any "Enable all" policies that are too permissive
DROP POLICY IF EXISTS "Enable all for service role" ON public.absentees;
DROP POLICY IF EXISTS "Enable all for service role" ON public.pending_registrations;
DROP POLICY IF EXISTS "Enable all for service role" ON public.semesters;
DROP POLICY IF EXISTS "Enable all for service role" ON public.users;
DROP POLICY IF EXISTS "Enable all for service role" ON public.students;


-- 3. CREATE SECURE RLS POLICIES
-- ================================================================

-- ============================================
-- USERS TABLE POLICIES
-- ============================================

-- Allow users to read their own data
CREATE POLICY "Users can view their own profile"
ON public.users
FOR SELECT
USING (auth.uid()::text = id::text OR email = auth.jwt()->>'email');

-- Allow admins to read all users
CREATE POLICY "Admins can view all users"
ON public.users
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Allow service role full access (for backend operations)
CREATE POLICY "Service role has full access to users"
ON public.users
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

-- Allow new user registration (insert only, not approved yet)
CREATE POLICY "Anyone can register"
ON public.users
FOR INSERT
WITH CHECK (true);


-- ============================================
-- ABSENTEES TABLE POLICIES
-- ============================================

-- Staff can view absentees they marked
CREATE POLICY "Staff can view their own absentees"
ON public.absentees
FOR SELECT
USING (
  marked_by = auth.jwt()->>'email'
  OR EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Staff can insert absentees
CREATE POLICY "Approved staff can insert absentees"
ON public.absentees
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND is_approved = true
    AND is_active = true
  )
);

-- Only admins can update absentee status
CREATE POLICY "Admins can update absentees"
ON public.absentees
FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Only admins can delete absentees
CREATE POLICY "Admins can delete absentees"
ON public.absentees
FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Service role full access
CREATE POLICY "Service role has full access to absentees"
ON public.absentees
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');


-- ============================================
-- STUDENTS TABLE POLICIES
-- ============================================

-- Approved users can view students
CREATE POLICY "Approved users can view students"
ON public.students
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND is_approved = true
    AND is_active = true
  )
);

-- Only admins can modify students
CREATE POLICY "Admins can modify students"
ON public.students
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Service role full access
CREATE POLICY "Service role has full access to students"
ON public.students
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');


-- ============================================
-- SEMESTERS TABLE POLICIES
-- ============================================

-- Approved users can view semesters
CREATE POLICY "Approved users can view semesters"
ON public.semesters
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND is_approved = true
    AND is_active = true
  )
);

-- Only admins can modify semesters
CREATE POLICY "Admins can modify semesters"
ON public.semesters
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Service role full access
CREATE POLICY "Service role has full access to semesters"
ON public.semesters
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');


-- ============================================
-- PASSWORD_RESET_REQUESTS TABLE POLICIES
-- ============================================

-- Users can only view their own reset requests
CREATE POLICY "Users can view their own reset requests"
ON public.password_reset_requests
FOR SELECT
USING (email = auth.jwt()->>'email');

-- Anyone can create a reset request (for forgot password)
CREATE POLICY "Anyone can create reset requests"
ON public.password_reset_requests
FOR INSERT
WITH CHECK (true);

-- Users can update their own reset requests (mark as used)
CREATE POLICY "Users can update their own reset requests"
ON public.password_reset_requests
FOR UPDATE
USING (email = auth.jwt()->>'email');

-- Admins can view all reset requests
CREATE POLICY "Admins can view all reset requests"
ON public.password_reset_requests
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Service role full access
CREATE POLICY "Service role has full access to reset requests"
ON public.password_reset_requests
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');


-- ============================================
-- PENDING_REGISTRATIONS TABLE POLICIES
-- ============================================

-- Only admins can view pending registrations
CREATE POLICY "Admins can view pending registrations"
ON public.pending_registrations
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Anyone can insert (for registration)
CREATE POLICY "Anyone can create pending registrations"
ON public.pending_registrations
FOR INSERT
WITH CHECK (true);

-- Only admins can update/delete
CREATE POLICY "Admins can modify pending registrations"
ON public.pending_registrations
FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
    AND is_approved = true
    AND is_active = true
  )
);

-- Service role full access
CREATE POLICY "Service role has full access to pending registrations"
ON public.pending_registrations
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');


-- ============================================
-- TIMETABLES TABLE POLICIES (SKIPPED - table doesn't exist)
-- ============================================
-- Note: The timetables table does not exist in your schema.
-- Timetable data is stored in semester-specific databases or files.
-- If you create a timetables table in the future, uncomment these policies:

-- Approved users can view timetables
-- CREATE POLICY "Approved users can view timetables"
-- ON public.timetables
-- FOR SELECT
-- USING (
--   EXISTS (
--     SELECT 1 FROM public.users
--     WHERE email = auth.jwt()->>'email'
--     AND is_approved = true
--     AND is_active = true
--   )
-- );

-- Only admins can modify timetables
-- CREATE POLICY "Admins can modify timetables"
-- ON public.timetables
-- FOR ALL
-- USING (
--   EXISTS (
--     SELECT 1 FROM public.users
--     WHERE email = auth.jwt()->>'email'
--     AND role = 'admin'
--     AND is_approved = true
--     AND is_active = true
--   )
-- );

-- Service role full access
-- CREATE POLICY "Service role has full access to timetables"
-- ON public.timetables
-- FOR ALL
-- USING (auth.jwt()->>'role' = 'service_role');


-- ================================================================
-- 4. VERIFICATION QUERIES
-- ================================================================
-- Run these to verify RLS is enabled and policies are active

-- Check RLS status on all tables
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check all policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ================================================================
-- NOTES:
-- ================================================================
-- 1. Service role bypasses RLS - this is for backend operations
-- 2. Authentication is based on JWT claims (email, role)
-- 3. All policies check for approved and active users
-- 4. Public access is limited to registration and password reset
-- 5. Admins have full access to all data
-- 6. Staff can only see data they created (absentees)
-- ================================================================
