# 🔐 Separate Login System - Student & Admin

## Overview
PriorityIQ now has **separate login portals** for students and college admins with proper access control.

## Login Portals

### 1. Student Login
**URL:** `http://127.0.0.1:5000/login`

**Features:**
- Standard student access
- Task management features
- AI chatbot, gamification, analytics
- Cannot access admin panel

**Access:**
- Any registered user without admin privileges
- Redirected to student dashboard after login

### 2. Admin Login
**URL:** `http://127.0.0.1:5000/admin-login`

**Features:**
- College admin access
- All student features PLUS admin panel
- Exam schedules, events, attendance, announcements
- Full administrative control

**Access:**
- Only users with `is_admin=TRUE` in database
- Redirected to dashboard with admin panel access

## How It Works

### Backend Validation (`auth_routes.py`)

```python
# request_otp endpoint now accepts login_type parameter
{
    "email": "user@example.com",
    "login_type": "student"  # or "admin"
}
```

**Validation Logic:**
1. Check if user exists
2. Check if user's admin status matches login type
3. **Student trying admin login** → "Access denied. Admin credentials required."
4. **Admin trying student login** → "Please use admin login."
5. Generate OTP only if validation passes

### Frontend Pages

**Student Login (`login.html`):**
- Sends `login_type: "student"`
- Link to admin login at bottom
- Standard blue theme

**Admin Login (`admin_login.html`):**
- Sends `login_type: "admin"`
- Purple gradient admin badge
- Link back to student login
- Validates admin credentials

## Usage Examples

### Student Login Flow
1. Go to `http://127.0.0.1:5000/login`
2. Enter student email
3. Click "Request OTP"
4. System validates: Is this a student account?
5. If yes → OTP generated
6. If admin account → "Please use admin login"

### Admin Login Flow
1. Go to `http://127.0.0.1:5000/admin-login`
2. Enter admin email
3. Click "Request OTP"
4. System validates: Is this an admin account?
5. If yes → OTP generated
6. If student account → "Access denied. Admin credentials required."

## Security Features

✅ **Role-Based Access Control** - Separate validation for each role
✅ **Proper Error Messages** - Clear feedback on access denial
✅ **Session Management** - Login type stored in session
✅ **URL Protection** - Admin pages require admin login
✅ **Cross-Login Prevention** - Students can't use admin portal, admins must use admin login

## Testing

### Test Student Login
```bash
# 1. Register as student (normal registration)
# 2. Go to http://127.0.0.1:5000/login
# 3. Enter student email
# 4. Should get OTP ✅
# 5. Try http://127.0.0.1:5000/admin-login with same email
# 6. Should get "Access denied" ✅
```

### Test Admin Login
```bash
# 1. Make user admin: python make_admin.py
# 2. Go to http://127.0.0.1:5000/admin-login
# 3. Enter admin email
# 4. Should get OTP ✅
# 5. Try http://127.0.0.1:5000/login with same email
# 6. Should get "Please use admin login" ✅
```

## Navigation

**From Student Login:**
- "Admin Login →" link at bottom
- Takes to `/admin-login`

**From Admin Login:**
- "← Back to Student Login" link
- Takes to `/login`

## Routes Summary

| Route | Purpose | Access |
|-------|---------|--------|
| `/login` | Student login portal | Everyone |
| `/admin-login` | Admin login portal | Everyone (validates admin status) |
| `/` | Dashboard | Logged-in users |
| `/admin` | Admin panel | Logged-in admins only |

## Error Messages

| Scenario | Message |
|----------|---------|
| Student tries admin login | "Access denied. Admin credentials required." |
| Admin tries student login | "Please use admin login." |
| Email not registered | "Email not registered. Please register first." |
| Invalid email format | "Valid email is required" |

## Benefits

1. **Clear Separation** - Students and admins have distinct entry points
2. **Better UX** - Users know which portal to use
3. **Enhanced Security** - Role validation at login stage
4. **Professional** - Separate portals look more enterprise-grade
5. **Scalable** - Easy to add more role types in future

## Implementation Files

- `routes/auth_routes.py` - Backend validation logic
- `templates/login.html` - Student login page
- `templates/admin_login.html` - Admin login page (NEW)
- `app.py` - Route registration

## Quick Start

```bash
# Start the app
python app.py

# Student Login
http://127.0.0.1:5000/login

# Admin Login
http://127.0.0.1:5000/admin-login
```

---

**Status:** ✅ COMPLETE
**Security:** 🔒 Role-based access control implemented
**Ready for Demo:** ✅ YES
