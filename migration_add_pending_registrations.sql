-- Migration: Add pending_registrations table
-- Run this in your Supabase SQL Editor to fix the registration OTP issue

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

-- Enable Row Level Security (RLS)
ALTER TABLE pending_registrations ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Enable all for service role" ON pending_registrations;

-- Create policy to allow service role to access everything
CREATE POLICY "Enable all for service role" ON pending_registrations
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- BUCKET MANAGEMENT FEATURE
-- ============================================================================
-- 
-- NEW FEATURE: Administrators can now delete entire storage buckets from the UI
--
-- Available Buckets:
--   1. pending_absentee  - Stores pending absentee submissions
--   2. approved_absentee - Stores approved absentee records
--   3. rejected_absentee - Stores rejected absentee records
--
-- Admin Interface:
--   - Navigate to "Manage Absentees" page
--   - In the "Cloud Storage" section, use "Bucket Management" buttons
--   - Options available:
--     * Clear Pending   - Deletes all files from pending_absentee bucket
--     * Clear Approved  - Deletes all files from approved_absentee bucket
--     * Clear Rejected  - Deletes all files from rejected_absentee bucket
--     * Clear ALL       - Deletes all files from ALL three buckets
--
-- API Endpoints:
--   POST /clear_bucket/<bucket_type>  - Clear specific bucket (pending/approved/rejected/all)
--   POST /clear_bucket_page           - Form handler for bucket clearing
--
-- Implementation:
--   - helpers/supabase_storage.py: Added clear_bucket(), clear_pending_bucket(), 
--     clear_approved_bucket(), clear_rejected_bucket(), clear_all_absentee_buckets()
--   - app.py: Added routes /clear_bucket/<type> and /clear_bucket_page
--   - templates/admin_absentees.html: Added bucket management UI with confirmation dialogs
--
-- Security:
--   - Only users with 'admin' role can clear buckets
--   - Confirmation dialogs prevent accidental deletion
--   - All operations are logged
--
-- Notes:
--   - Bucket clearing is permanent and cannot be undone
--   - This only affects storage files, not database records
--   - The database 'absentees' table records remain intact
-- ============================================================================
