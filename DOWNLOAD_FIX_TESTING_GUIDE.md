# DOWNLOAD BUTTON FIX - TESTING GUIDE

## ✅ Critical Bug Fixed

**Root Cause:** The code was using `session['absentees']` which throws a `KeyError` if the key doesn't exist in the session. This caused the entire download handler to fail silently.

**Fix Applied:** Changed to `session.get('absentees', [])` which safely returns an empty list if the key doesn't exist.

---

## 🧪 How to Test the Fix

### Step 1: Start the Application
```bash
python app.py
# or
python run.py
```

### Step 2: Login to the System
- Use your staff credentials
- Make sure you're logged in successfully

### Step 3: Mark Some Students Absent
1. Go to "Generate Absentee Sheet" page
2. Search for a course (e.g., CS1001)
3. Load students for that course
4. Select at least 1-2 students
5. Click "Mark Selected as Absent"
6. Verify they appear in the "Marked Absentees" section on the right

### Step 4: Test the Download
1. **IMPORTANT:** Select a **Semester** from the dropdown
2. Set an **Exam Date** for each course (or use the default)
3. Open Browser Developer Tools (**F12**)
4. Go to the **Console** tab
5. Click the **Download** button

### Step 5: Check Console Output
You should see logs like this in the console:
```
[DOWNLOAD] prepareExamDatesForSubmit() called
[DOWNLOAD] Found 1 course exam date inputs
[DOWNLOAD] Semester selected: 1
[DOWNLOAD] Form action: /absentee
[DOWNLOAD] Form method: POST
[DOWNLOAD] Removing 0 existing hidden date fields
[DOWNLOAD] Added hidden field: exam_date_CS1001 = 2026-02-23
[DOWNLOAD] Added 1 exam date fields to form
[DOWNLOAD] Final form data:
  semester_id = 1
  exam_date_CS1001 = 2026-02-23
  action = download_absentees
[DOWNLOAD] Returning true - form will submit
[DOWNLOAD BTN] Click event fired, isProcessing: false
[DOWNLOAD BTN] Setting loading state
```

### Step 6: Check Network Tab
1. In Developer Tools, click the **Network** tab
2. Look for a POST request to `/absentee`
3. Click on it and check:
   - **Status:** Should be `200 OK`
   - **Response Type:** Should be `application/pdf` or `application/zip`
   - **Size:** Should be > 50KB

### Step 7: Verify Download
- A file should automatically download to your Downloads folder
- Filename: `Absentee_Sheet_COURSECODE_DATE.pdf` (or `.zip` for multiple courses)
- Open the PDF and verify it contains the correct students

---

## 🔍 Diagnostic Endpoint (New!)

You can check your session state by visiting:
```
http://localhost:5000/debug/session-info
```

This will show:
```json
{
  "session_has_absentees_key": true,
  "absentees_count": 2,
  "absentees_sample": [
    {"roll_no": "B220001CS", "name": "Student 1", ...},
    ...
  ],
  "username": "your_username",
  "role": "staff",
  "session_keys": ["absentees", "username", "logged_in", ...]
}
```

If `absentees_count` is 0, you need to mark students absent first.

---

## ❌ If Download Still Fails

### Check Browser Console for Errors
Look for any red error messages. Common issues:
- `[DOWNLOAD] ERROR: Semester not selected` → Select a semester
- `[DOWNLOAD] ERROR: Form not found!` → Refresh the page
- JavaScript errors → Check if there's a syntax error

### Check Backend Logs
You should see in your terminal:
```
============================================================
[DOWNLOAD ABSENTEES] Request received
Session absentees count: 2
Session keys: ['absentees', 'username', 'logged_in', ...]
============================================================
[DOWNLOAD ABSENTEES] Semester ID: 1
[DOWNLOAD ABSENTEES] Found 1 course exam dates
  - CS1001: 2026-02-23
[DOWNLOAD ABSENTEES] Grouped absentees by course: ['CS1001']
[DOWNLOAD ABSENTEES] Generating sheet for CS1001 with 2 absentee(s)...
[DOWNLOAD ABSENTEES] HTML generated: True, Message: None
[DOWNLOAD ABSENTEES] Converting CS1001 to PDF...
[DOWNLOAD ABSENTEES] PDF generated: True, Size: 52431 bytes
[DOWNLOAD ABSENTEES] Total PDFs generated: 1
[DOWNLOAD ABSENTEES] Sending single PDF: Absentee_Sheet_CS1001_2026-02-23.pdf
```

If you see any errors in the logs, report them.

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No absentees in session" | Mark students absent first |
| "Semester not selected" | Select semester from dropdown |
| "KeyError: 'absentees'" | **FIXED** - Should not happen anymore |
| "Failed to generate HTML" | Check database connection |
| "Failed to convert to PDF" | Check `xhtml2pdf` is installed |
| Button stays loading forever | Check timeout (30s), then should reset |

---

## 📋Test Checklist

- [ ] Can login successfully
- [ ] Can search for courses
- [ ] Can load students for a course
- [ ] Can mark students as absent
- [ ] Absentees appear in the right panel
- [ ] Can select a semester
- [ ] Can set exam dates
- [ ] Download button shows correct console logs
- [ ] Network request shows status 200
- [ ] PDF file downloads successfully
- [ ] PDF contains correct students

---

## 🚀 Changes Made

1. **Fixed KeyError in session handling** (3 places)
   - `session['absentees']` → `session.get('absentees', [])`
   
2. **Added comprehensive logging**
   - Form validation logging
   - Form data inspection
   - Session state logging
   
3. **Added session diagnostic endpoint**
   - `/debug/session-info` to check session state
   
4. **Improved error handling**
   - Better error messages
   - More detailed exception logging
   
5. **Created test script**
   - `test_download_absentees.py` to validate logic

---

## 📞 Still Not Working?

If the download still doesn't work after following all steps:

1. Copy and paste the **complete browser console output**
2. Copy and paste the **backend terminal output**
3. Take a screenshot of the **Network tab** showing the POST request
4. Report what happens when you click Download

This information will help identify any remaining issues.
