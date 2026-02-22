# Download Button Troubleshooting Guide

## Issue
The "Download" button on the Generate Absentee Sheet page shows "Generating Sheets..." but never completes the download.

## Root Cause Investigation Steps

### Step 1: Check Browser Console for Errors
1. Open the page in your browser
2. Press **F12** to open Developer Tools
3. Click the **Console** tab
4. Look for any red error messages
5. Click the **Download** button and watch the console for messages starting with `[DOWNLOAD]` or `[DOWNLOAD BTN]`

**What to look for:**
- `[DOWNLOAD] prepareExamDatesForSubmit() called` - Form handler is firing
- `[DOWNLOAD] ERROR: Semester not selected` - User hasn't selected semester (FIX: Select a semester)
- `[DOWNLOAD] Found X course exam date inputs` - Should be > 0 if there are absentees
- `[DOWNLOAD BTN] Click event fired` - Button click is registered
- `[DOWNLOAD BTN] Setting loading state` - Loading animation should show
- Any red error messages about invalid code

### Step 2: Check Network Tab for Request/Response
1. Open Developer Tools (F12)
2. Click the **Network** tab
3. Check the checkbox for **Preserve log** (important!)
4. Click the **Download** button
5. Look for a POST request to `/absentee` in the network tab

**What to check:**
- **Status Code**: 
  - 200 = Success (file should download)
  - 302/303 = Redirect (error occurred, being redirected)
  - 500 = Server error
  - No request = Form not submitting
  
- **Response Headers**:
  - Look for `Content-Type: application/pdf` (or application/zip)
  - Look for `Content-Disposition: attachment; filename=...`
  - If content-type is `text/html`, file won't download
  
- **Response Size**: Should be > 100KB for a PDF

### Step 3: Check Backend Logs
1. Look at your application logs/terminal output
2. Search for lines starting with `[DOWNLOAD ABSENTEES]`
3. Expected sequence should be:
   ```
   ============================================================
   [DOWNLOAD ABSENTEES] Request received
   [DOWNLOAD ABSENTEES] Session absentees count: X
   [DOWNLOAD ABSENTEES] Semester ID: ...
   [DOWNLOAD ABSENTEES] Found X course exam dates
   [DOWNLOAD ABSENTEES] Grouped absentees by course: [...]
   [DOWNLOAD ABSENTEES] Generating sheet for COURSE_CODE...
   [DOWNLOAD ABSENTEES] HTML generated: True
   [DOWNLOAD ABSENTEES] Converting to PDF...
   [DOWNLOAD ABSENTEES] PDF generated: True, Size: XXXXX bytes
   [DOWNLOAD ABSENTEES] Total PDFs generated: X
   [DOWNLOAD ABSENTEES] Sending single PDF: Absentee_Sheet_...pdf
   ```

## Common Issues & Fixes

### Issue 1: "ERROR: Semester not selected" in Console
**Fix**: Select a semester from the "Semester" dropdown before clicking Download

### Issue 2: Only 1 course exam date input found, but have multiple courses
**Problem**: Exam date inputs might not be loading properly
**Fix**: 
- Refresh the page (Ctrl+F5)
- Make sure you've properly added absentees from multiple courses
- Check that each course section has an exam date input

### Issue 3: POS T request shows Status 302 (Redirect)
**Problem**: Backend returned a redirect (usually due to error)
**How to debug**:
1. In Network tab, click on the redirected request
2. Click the **Preview** tab to see the error message
3. Common error: "Please select a semester before downloading"

### Issue 4: POST request succeeds (status 200) but no download happens
**Problem**: Either:
- Response is HTML instead of PDF (MIME type issue)
- Browser is blocking download
- File size too large

**How to debug**:
1. In Network tab, click on the POST request
2. Click **Response** tab
3. If you see HTML code, the backend returned an error page
4. If you see binary data (gibberish), it's a PDF
5. Check **Response Headers** for `Content-Type`

### Issue 5: Backend logs don't show `[DOWNLOAD ABSENTEES]` at all
**Problem**: Request never reached backend
**Possible causes**:
- Form not submitting (JavaScript error preventing it)
- onclick handler returning false
- Network issue

**How to fix**:
1. Check browser console for errors
2. Check Network tab to see if ANY POST request is sent
3. Try opening browser console and running: `document.getElementById('absenteeActionsForm').submit()`
4. This will force a form submit bypassing the onclick handler

## Manual Testing

### Test 1: Verify Form Submission Works
In browser console, paste and run:
```javascript
document.getElementById('absenteeActionsForm').submit();
```

This bypasses all JavaScript and submits the form directly.

### Test 2: Check Session State
In browser console, paste and run:
```javascript
fetch('/api/session-info').then(r => r.json()).then(d => console.log('Session absentees:', d))
```

(This requires API endpoint to exist)

## What Was Fixed Recently

1. ✅ Added comprehensive console logging to track form submission
2. ✅ Fixed button timeout to properly reset after 30 seconds (previously could get stuck forever)
3. ✅ Improved exam date field handling to ensure all course dates are captured
4. ✅ Added detailed backend logging to trace PDF generation flow
5. ✅ Fixed loading state management to prevent duplicate requests

## Backend Changes (for reference)
- Added debug logging throughout `download_absentees` action handler
- Added try/except wrapping around PDF generation
- Added detailed logging for exam date collection, HTML generation, PDF conversion

## Frontend Changes (for reference)  
- Added `[DOWNLOAD]` console logging to prepareExamDatesForSubmit() function
- Added `[DOWNLOAD BTN]` console logging to button click handler
- Fixed button timeout logic to reset after 30 seconds regardless of download completion
- Fixed variable scoping for separate tracking of download vs upload button states

## Still Need Help?

If the above steps don't resolve the issue:

1. **Open an issue with the following info:**
   - Screenshot of browser console (F12 > Console tab) while clicking download
   - Screenshot of Network tab showing the POST request
   - First 20 lines of backend logs when clicking download
   - How many courses have absentees?
   - How many absentees total?
   - Error messages if any

2. **Quick Fixes to Try:**
   - Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   - Clear browser cache and cookies
   - Try in a different browser
   - Try with only 1-2 absentees at first

## Performance Notes

PDF generation from HTML can take 5-15 seconds depending on:
- Number of absentees
- Complexity of HTML/styling
- Server resources
- Network latency

The button will automatically reset after 30 seconds, so if it's taking that long, something is likely hanging.
