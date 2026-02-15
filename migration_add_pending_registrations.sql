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
