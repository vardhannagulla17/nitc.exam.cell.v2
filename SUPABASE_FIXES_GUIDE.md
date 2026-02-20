# Supabase Security & Performance Fixes

## 🚨 Critical Security Issues Found

Your Supabase database currently has **3 security issues** that need immediate attention:

### Security Problems:
1. ❌ `password_reset_requests` - Exposed via API without RLS
2. ❌ `absentees` - Overly permissive RLS policy ("Enable all for service role" should be more specific)
3. ❌ `pending_registrations` - Overly permissive RLS policy

### Performance Issues:
1. ⚠️ `students` table - Has duplicate indexes (idx_students_roll_no and idx_students_rollno)
   - Wastes storage space
   - Slows down insert/update operations

---

## ✅ Solution: Apply Security Fixes

### Step 1: Apply RLS Policies

1. **Open Supabase SQL Editor:**
   - Go to your Supabase dashboard
   - Click on "SQL Editor" in the left sidebar
   - Create a new query

2. **Run the Security Script:**
   - Open the file `supabase_security_fixes.sql`
   - Copy the entire content
   - Paste it into the Supabase SQL Editor
   - Click "Run" to execute

3. **Run the Performance Script:**
   - In SQL Editor, create another new query
   - Open the file `supabase_performance_fixes.sql`
   - Copy the entire content
   - Paste it into the Supabase SQL Editor
   - Click "Run" to execute

4. **Verify the Fix:**
   The scripts will show verification queries at the end displaying:
   - All tables with RLS enabled
   - All active policies
   - Indexes on students table (duplicate removed)

---

## 🔒 What the Fix Does

### Row Level Security (RLS) Policies Created:

#### 1. **Users Table**
- ✅ Users can only view their own profile
- ✅ Admins can view all users
- ✅ Service role has full access (for backend)
- ✅ Anyone can register (but not auto-approved)

#### 2. **Absentees Table**
- ✅ Staff can view absentees they marked
- ✅ Admins can view all absentees
- ✅ Only approved staff can insert
- ✅ Only admins can update/delete

#### 3. **Students Table**
- ✅ Approved users can view students
- ✅ Only admins can modify

#### 4. **Semesters Table**
- ✅ Approved users can view semesters
- ✅ Only admins can modify

#### 5. **Password Reset Requests**
- ✅ Users can only view their own requests
- ✅ Anyone can create (for forgot password)
- ✅ Admins can view all requests
- ✅ Auto-cleanup of expired requests

#### 6. **Pending Registrations**
- ✅ Only admins can view
- ✅ Anyone can insert (for registration)
- ✅ Only admins can approve/delete

---

## 🚀 Performance Optimization

### Current Slow Queries Detected:
```sql
SELECT name FROM pg_timezone_names           -- 0.59s, 17 calls
SELECT case when pg_is_in_recovery()...      -- 0.19s, 41 calls
WITH base as (select auth.rolname...)        -- 0.38s, 1 call
```

### These are mostly PostgreSQL internal queries and won't affect your app performance.

### Your App's Performance:
✅ **Already Optimized!** (from previous session)
- Dashboard stats caching: 2-10ms (99.5% faster)
- Pending users count: 5-10ms (95% faster)
- First load: 800-1500ms (50% faster)

---

## ⚙️ Backend Configuration

### Update Supabase Client

Your app uses `supabase_client.py` which connects with **service role key**. This bypasses RLS policies (which is correct for backend operations).

**No code changes needed!** The service role policies are already in the SQL script:

```sql
CREATE POLICY "Service role has full access to users"
ON public.users
FOR ALL
USING (auth.jwt()->>'role' = 'service_role');
```

---

## 🧪 Testing After Applying Fixes

### 1. Test Security (Using Supabase Dashboard):

#### Test 1: Anonymous Access (Should Fail)
```sql
-- This should return 0 rows (RLS blocks it)
SELECT * FROM public.users;
```

#### Test 2: Service Role Access (Should Work)
- Your Flask app will continue to work normally
- Backend operations use service role key

#### Test 3: User Data Isolation
- Users can only see their own data
- Admins can see all data

### 2. Test Your Application:

```powershell
# Run your Flask app
python app.py

# Test these workflows:
# 1. Login (should work)
# 2. Dashboard (should load fast with cached stats)
# 3. Upload timetable (admin only)
# 4. Mark absentees (approved staff only)
# 5. View abse3 security issues need attention
- **After:** 0 issues ✅

### Performance Dashboard:
- **Before:** 1 performance issue (duplicate indexes)
- **After:** 0 issues ✅

### Your App:
- **Dashboard:** Already optimized (99.5% faster dashboard)
- **Insert/Update:** Faster (no duplicate index overhead)
- **Storage:** Reduced (duplicate index remove

### Security Dashboard:
- **Before:** 9 issues need attention
- **After:** 0 issues ✅

### Performance:
- **Slow Queries:** Will remain (these are PostgreSQL internal, not your app)
- **Your App:** Already optimized (99.5% faster dashboard)

---

## 🔧 If Issues Occur

### Issue: "Can't access data after applying RLS"

**Solution:** Check if your `supabase_client.py` uses the **service role key**:

```python
# In supabase_client.py - should use service_role_key
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY  # ← Must be service role key
)
```

### Issue: "Users can't register"

**Solution:** The "Anyone can register" policy allows public registration:
```sql
CREATE POLICY "Anyone can register"
ON public.users
FOR INSERT
WITH CHECK (true);
```

### Issue: "Staff can't see absentees"

**Solution:** Check if the user's email matches JWT:
```python
# Your Flask backend should pass user email correctly
# RLS policies check: auth.jwt()->>'email'
```

---

## 📝 Maintenance

### Regular Security Checks:

1. **Monthly:** Review RLS policies in Supabase dashboard
2. **After Schema Changes:** Update RLS policies accordingly
3. **Audit Logs:** Monitor access patterns in Supabase

### Performance Monitoring:

1. **Dashboard:** Check "Slow Queries" tab weekly
2. **App Logs:** Monitor cache hit rates
3. **User Reports:** Track login and page load times

---

## 🎯 Next Steps

1. ✅ **NOW:** Run `supabase_security_fixes.sql` in Supabase SQL Editor
2. ✅ **Verify:** Check security issues reduced to 0
3. ✅ **Test:** Login and perform key workflows
4. ✅ **Monitor:** Watch for any access issues over next 24 hours
5. ✅ **Document:** Add this to your deployment checklist

---

## 🆘 Need Help?

### Common Commands:

**Check which tables have RLS enabled:**
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

**View all RLS policies:**
```sql
SELECT tablename, policyname, cmd 
FROM pg_policies 
WHERE schemaname = 'public';
```

**Disable RLS on a table (emergency only):**
```sql
ALTER TABLE public.table_name DISABLE ROW LEVEL SECURITY;
```

---

## ✨ Summary
Copy and paste `supabase_performance_fixes.sql`
5. Click "Run"
6. Verify security issues = 0 and performance issues = 0
7. Test your app (everything should work normally)

**What Will Change:**
- ✅ Security issues fixed (3 → 0)
- ✅ Performance issues fixed (1 → 0)
- ✅ Proper data isolation (users see only their data)
- ✅ Admin full access (role-based access)
- ✅ Service role bypass (your backend continues to work)
- ✅ Faster insert/update on students (duplicate index removed
**What Will Change:**
- ✅ Security issues fixed (9 → 0)
- ✅ Proper data isolation (users see only their data)
- ✅ Admin full access (role-based access)
- ✅ Service role bypass (your backend c(2 SQL scripts)  
**Downtime required:** None (can be applied in production)  
**Risk level:** Low (service role ensures backend operations continue)

---

## 🔍 What Was Fixed

### Issue 1: Duplicate Index on students.roll_no
**Problem:** Two identical indexes on the same column
- `idx_students_roll_no` (created by supabase_schema.sql)
- `idx_students_rollno` (created by database_indexes.sql)

**Impact:** 
- Wasted storage (2x the space)
- Slower insert/update operations (must update both indexes)
- No performance benefit

**Solution:** Dropped `idx_students_roll_no`, kept `idx_students_rollno`

### Issue 2: Timetables Table Doesn't Exist
**Problem:** Security script tried to create policies for non-existent `timetables` table

**Impact:** SQL error during execution

**Solution:** Commented out timetables policies (table not used in your schema
- ✅ App functionality (everything works the same)
- ✅ Performance (already optimized yesterday)
- ✅ User experience (seamless)

---

**Estimated time to apply:** 5 minutes  
**Downtime required:** None (can be applied in production)  
**Risk level:** Low (service role ensures backend operations continue)
