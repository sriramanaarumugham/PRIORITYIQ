# 🔧 Exam Adding - Troubleshooting Guide

## Changes Made

### Backend (`admin_routes.py`)
- Added error handling with try-catch
- Added console logging: `[DEBUG] Adding exam: {data}`
- Added success logging: `[DEBUG] Exam added successfully with ID: {exam_id}`
- Returns exam_id on success
- Returns error message on failure

### Frontend (`admin.html`)
- Added console.log for request data
- Added console.log for response
- Added error handling with try-catch
- Shows specific error messages in alerts

## How to Debug

### Step 1: Open Browser Console
```
Press F12 → Go to Console tab
```

### Step 2: Try Adding an Exam
Fill the form and click "Add Exam"

### Step 3: Check Console Output
You'll see:
```
Adding exam: {dept_id: 1, subject_name: "Math", ...}
Response: {success: true, exam_id: 5}
```

OR if error:
```
Adding exam: {dept_id: 1, subject_name: "Math", ...}
Response: {success: false, message: "Error details here"}
```

### Step 4: Check Terminal/CMD
In the terminal where `python app.py` is running, you'll see:
```
[DEBUG] Adding exam: {'dept_id': 1, 'subject_name': 'Math', ...}
[DEBUG] Exam added successfully with ID: 5
```

OR if error:
```
[DEBUG] Adding exam: {'dept_id': 1, 'subject_name': 'Math', ...}
[ERROR] Failed to add exam: <error details>
```

## Common Issues & Solutions

### Issue 1: "Admin access required"
**Cause:** Not logged in as admin
**Solution:** 
1. Logout
2. Login at `/admin-login` with admin credentials
3. Try again

### Issue 2: Empty department dropdown
**Cause:** Departments not loaded
**Solution:**
1. Run `python setup_admin.py` again
2. Refresh page
3. Check browser console for errors

### Issue 3: Database connection error
**Cause:** MySQL not running or wrong credentials
**Solution:**
1. Start MySQL server
2. Check `.env` file for correct DB credentials
3. Test connection: `python -c "from db_connection import get_db_connection; print(get_db_connection())"`

### Issue 4: "Failed to add exam" with no details
**Cause:** Missing required fields
**Solution:**
1. Make sure all required fields are filled
2. Check date format (YYYY-MM-DD)
3. Check time format (HH:MM)
4. Duration must be a number

## Test Checklist

✅ **Before Testing:**
- [ ] MySQL is running
- [ ] Logged in as admin
- [ ] On `/admin` page
- [ ] Browser console is open (F12)
- [ ] Terminal with `python app.py` is visible

✅ **Test Steps:**
1. [ ] Select department from dropdown
2. [ ] Enter subject name
3. [ ] Select exam date
4. [ ] Select exam time
5. [ ] Enter duration (e.g., 180)
6. [ ] Enter room number (optional)
7. [ ] Click "Add Exam"
8. [ ] Check alert message
9. [ ] Check browser console
10. [ ] Check terminal output
11. [ ] Verify exam appears in table below

## Expected Behavior

**Success:**
- Alert: "Exam added successfully!"
- Form clears
- Exam appears in table immediately
- Console: `Response: {success: true, exam_id: X}`
- Terminal: `[DEBUG] Exam added successfully with ID: X`

**Failure:**
- Alert: "Error: <specific error message>"
- Form stays filled
- Console: `Response: {success: false, message: "..."}`
- Terminal: `[ERROR] Failed to add exam: ...`

## Quick Fix Commands

```bash
# Restart app
python app.py

# Check database tables
python -c "from db_connection import get_db_connection; conn = get_db_connection(); cursor = conn.cursor(); cursor.execute('SHOW TABLES'); print([t[0] for t in cursor.fetchall()])"

# Check departments
python -c "from db_connection import get_db_connection; conn = get_db_connection(); cursor = conn.cursor(dictionary=True); cursor.execute('SELECT * FROM departments'); print(cursor.fetchall())"

# Check exams
python -c "from db_connection import get_db_connection; conn = get_db_connection(); cursor = conn.cursor(dictionary=True); cursor.execute('SELECT * FROM exam_schedules'); print(cursor.fetchall())"
```

## Still Not Working?

Share the following information:
1. Browser console output (screenshot)
2. Terminal output (copy-paste)
3. Steps you followed
4. Error message shown

---

**Status:** ✅ Enhanced error handling added
**Debugging:** Console and terminal logging enabled
**Next:** Test and check console/terminal for errors
