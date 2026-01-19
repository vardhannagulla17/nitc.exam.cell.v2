"""Test Supabase users table connection"""
import os
os.environ['SUPABASE_URL'] = "https://bnldcbnhgrtkjcdaahwe.supabase.co"
os.environ['SUPABASE_ANON_KEY'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGRjYm5oZ3J0a2pjZGFhaHdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ5NDQyNjcsImV4cCI6MjA4MDUyMDI2N30.sjP9UqATN1mvwI5OqYS8Tbmekia5V-rdEtPuLmwvFFo"

from supabase_client import supabase
from werkzeug.security import check_password_hash, generate_password_hash

print('Testing Supabase connection...')
try:
    # Test login for vardhan
    print('\nTesting login for vardhan...')
    result = supabase.table('users').select('id, username, password_hash, role').eq('username', 'vardhan').execute()
    
    if result.data and len(result.data) > 0:
        user = result.data[0]
        print(f"User found: {user['username']}")
        print(f"Role: {user['role']}")
        
        # Test password
        password_correct = check_password_hash(user['password_hash'], 'vardhan123')
        print(f"Password 'vardhan123' correct: {password_correct}")
        
        if password_correct:
            print("✅ Login would succeed!")
        else:
            print("❌ Password mismatch - need to reset password")
    else:
        print("❌ User not found")
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
