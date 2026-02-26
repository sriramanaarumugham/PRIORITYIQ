# 🎓 Admin Registration Guide

## ✅ NEW: Separate Admin Credentials (DB Whitelist)

Admin access is now controlled by a separate `admin_credentials` table (email whitelist).

## How to Enable an Admin

### Step 1: Register the User
```
http://127.0.0.1:5000/register
```

### Step 2: Whitelist the Admin Email
Run:
```
python add_admin_credential.py
```
Enter the email you want to allow as admin.

### Step 3: Login as Admin
```
http://127.0.0.1:5000/admin-login
```
- Enter the whitelisted email
- Get OTP and verify
- Access admin panel ✅

## Role Options

| Role | Access Level | Login Portal |
|------|-------------|--------------|
| **Student** | Task management only | `/login` |
| **Admin (College Staff)** | Admin access via whitelist | `/admin-login` |
| Professional | Task management only | `/login` |
| Freelancer | Task management only | `/login` |
| Manager | Task management only | `/login` |
| Other | Task management only | `/login` |

## Complete Flow Example

```bash
# 1. Start app
python app.py

# 2. Register user
# Browser: http://127.0.0.1:5000/register
# - Name: John Doe
# - Email: admin@college.edu
# - Phone: 1234567890
# - Role: any
# - Click Register

# 3. Whitelist admin email
# python add_admin_credential.py
# - Enter: admin@college.edu

# 4. Login as Admin
# Browser: http://127.0.0.1:5000/admin-login
# - Enter: admin@college.edu
# - Get OTP
# - Verify and login

# 5. Access Admin Panel
# Click "🎓 Admin" in navigation
# Manage exams, events, attendance, announcements
```

## How It Works

**Backend Logic (`auth_routes.py`):**
```python
# Admin access is checked against admin_credentials
# (email whitelist), not role selection
```

**Login Validation:**
- Admin role users → Can only use `/admin-login`
- Other roles → Can only use `/login`
- System validates role at login time

## Benefits

✅ **No command-line needed** - Register directly through web form
✅ **Self-service** - Admins can register themselves
✅ **Clear role selection** - "Admin (College Staff)" option
✅ **Automatic setup** - is_admin flag set automatically
✅ **Secure** - Still validates at login time

## Testing

### Test Admin Registration
1. Go to `/register`
2. Select "Admin (College Staff)" as role
3. Complete registration
4. Try `/login` → Should say "Please use admin login"
5. Try `/admin-login` → Should work ✅

### Test Student Registration
1. Go to `/register`
2. Select "Student" as role
3. Complete registration
4. Try `/admin-login` → Should say "Access denied"
5. Try `/login` → Should work ✅

## Notes

- **Role is now required** - Must select a role during registration
- **Admin role** automatically grants admin privileges
- **No script needed** - No need to run `make_admin.py` anymore
- **Backward compatible** - Old `make_admin.py` script still works

---

**Status:** ✅ COMPLETE
**Registration:** Direct admin registration enabled
**Ready for Demo:** ✅ YES
