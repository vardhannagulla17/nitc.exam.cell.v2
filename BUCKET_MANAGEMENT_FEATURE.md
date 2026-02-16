# Bucket Management Feature

## Overview
The Bucket Management feature allows administrators to delete all files from Supabase storage buckets through the web interface. This is useful for clearing old data, testing, or managing storage space.

## Available Buckets

### 1. Pending Absentee Bucket (`pending_absentee`)
- Stores absentee submissions that are awaiting admin review
- Files are in JSON format containing student absentee information
- Cleared automatically when records are approved/rejected

### 2. Approved Absentee Bucket (`approved_absentee`)
- Stores approved absentee records
- Contains finalized absentee data ready for download
- Used for generating consolidated reports

### 3. Rejected Absentee Bucket (`rejected_absentee`)
- Stores rejected absentee submissions
- Archives rejected records for audit purposes

## How to Use

### Access the Feature
1. Log in as an **Administrator**
2. Navigate to **"Manage Absentees"** page
3. Locate the **"Cloud Storage"** card
4. Find the **"Bucket Management"** section

### Clear Individual Buckets
- **Clear Pending** - Delete all files from pending bucket
- **Clear Approved** - Delete all files from approved bucket
- **Clear Rejected** - Delete all files from rejected bucket

Each button shows the current file count in parentheses.

### Clear All Buckets
Use the **"Clear ALL Buckets"** button to delete files from all three buckets at once.

### Confirmation Dialogs
- Each action requires confirmation
- Shows the number of files that will be deleted
- "Clear ALL" has an extra strong warning

## API Endpoints

### POST /clear_bucket/<bucket_type>
Clear a specific bucket via API.

**Parameters:**
- `bucket_type`: One of `pending`, `approved`, `rejected`, or `all`

**Response:**
```json
{
  "success": true,
  "message": "Successfully deleted N files from bucket_name bucket",
  "deleted_count": N
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:5000/clear_bucket/pending \
  -H "Content-Type: application/json" \
  -b "session_cookie"
```

### POST /clear_bucket_page
HTML form handler for bucket clearing.

**Form Actions:**
- `action=clear_pending`
- `action=clear_approved`
- `action=clear_rejected`
- `action=clear_all`

## Security

### Authorization
- **Only administrators** can clear buckets
- Regular staff users cannot access this feature
- Requires active admin session

### Safety Features
1. **Confirmation Dialogs** - Prevents accidental deletion
2. **File Counts** - Shows exactly what will be deleted
3. **Role Checking** - Validates admin role on backend
4. **Audit Trail** - All operations are logged

### What Gets Deleted
- ✅ Storage bucket files (JSON files in Supabase Storage)
- ❌ Database records (absentees table remains intact)
- ❌ User data
- ❌ Semester data

## Implementation Details

### Files Modified

#### 1. `helpers/supabase_storage.py`
Added methods to `AbsenteeStorage` class:
```python
def clear_bucket(bucket_name: str) -> tuple
def clear_pending_bucket() -> tuple
def clear_approved_bucket() -> tuple
def clear_rejected_bucket() -> tuple
def clear_all_absentee_buckets() -> dict
```

#### 2. `app.py`
Added routes:
```python
@app.route('/clear_bucket/<bucket_type>', methods=['POST'])
@app.route('/clear_bucket_page', methods=['GET', 'POST'])
```

#### 3. `templates/admin_absentees.html`
Added bucket management UI section with:
- Individual bucket clear buttons
- Clear all buckets button
- File count displays
- Warning messages

#### 4. `migration_add_pending_registrations.sql`
Added comprehensive documentation about the feature.

## Usage Examples

### Example 1: Clear Pending Bucket
```python
from helpers.supabase_storage import absentee_storage

# Clear pending bucket
success, message, count = absentee_storage.clear_pending_bucket()
print(f"{message} - Deleted {count} files")
```

### Example 2: Clear All Buckets
```python
from helpers.supabase_storage import absentee_storage

# Clear all buckets
results = absentee_storage.clear_all_absentee_buckets()
for bucket_name, (success, message, count) in results.items():
    print(f"{bucket_name}: {message}")
```

### Example 3: Using the UI
1. Navigate to "Manage Absentees"
2. Scroll to "Bucket Management"
3. Click "Clear Pending (5)"
4. Confirm the dialog
5. Wait for success message

## Testing

### Test Bucket Deletion
```python
# In Python console or test script
from helpers.supabase_storage import absentee_storage

# List files before
pending_before = absentee_storage.list_pending_absentees()
print(f"Files before: {len(pending_before)}")

# Clear bucket
success, message, count = absentee_storage.clear_pending_bucket()
print(f"Result: {message}")

# List files after
pending_after = absentee_storage.list_pending_absentees()
print(f"Files after: {len(pending_after)}")
```

### Test Script
You can use `check_approved_bucket.py` to verify bucket contents:
```bash
python check_approved_bucket.py
```

## Troubleshooting

### Issue: "Database not configured"
**Solution:** Check environment variables:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

### Issue: "Access denied"
**Solution:** Ensure you're logged in as an administrator.

### Issue: Buckets not clearing
**Possible causes:**
1. Network connectivity issues
2. Supabase credentials expired
3. Insufficient permissions
4. Bucket doesn't exist

**Debug steps:**
1. Check browser console for errors
2. Check server logs for API errors
3. Verify Supabase configuration
4. Test with `check_approved_bucket.py`

## Best Practices

### When to Clear Buckets
- ✅ After semester ends (archive then clear)
- ✅ During testing/development
- ✅ When storage space is low
- ✅ To remove old rejected records

### When NOT to Clear Buckets
- ❌ During active exam period
- ❌ Before downloading/archiving data
- ❌ When other admins are working
- ❌ Without proper backups

### Recommended Workflow
1. **Download** consolidated reports first
2. **Verify** downloads are complete
3. **Backup** important data
4. **Clear** buckets
5. **Confirm** success

## Future Enhancements

Possible improvements:
- [ ] Schedule automatic bucket clearing
- [ ] Archive to local storage before clearing
- [ ] Selective file deletion (by date/course)
- [ ] Bucket size/usage statistics
- [ ] Restore deleted files (implement soft delete)
- [ ] Email notifications on bucket clear

## Related Documentation

- See `OTP_FIX_README.md` for registration features
- See `PROJECT_COMPLETE_EXPLANATION.txt` for full project overview
- See `supabase_schema.sql` for database schema
- See `helpers/supabase_storage.py` for implementation details

## Support

For issues or questions:
1. Check server logs in terminal
2. Review browser console for frontend errors
3. Test Supabase connection with `check_approved_bucket.py`
4. Verify admin role in database

---

**Last Updated:** February 16, 2026
**Feature Version:** 1.0
**Status:** Production Ready ✅
