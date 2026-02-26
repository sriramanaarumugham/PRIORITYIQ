# Registration System Setup Guide

## Changes Made

### 1. Database Updates
- Added fields to `users` table:
  - `phone` VARCHAR(15) - Phone number (unique)
  - `role` VARCHAR(50) - User role (Student, Professional, etc.)
  - `age` INT - User age
  - `gender` VARCHAR(10) - User gender

### 2. New Features
- ✅ Complete registration form with all fields
- ✅ Email and phone uniqueness validation
- ✅ OTP displayed in popup modal
- ✅ Separate registration and login pages
- ✅ Users must register before login

### 3. User Flow
1. User visits `/register`
2. Fills form: Name, Email, Phone, Role, Age, Gender
3. Clicks "Register" → Account created
4. Redirected to `/login`
5. Enters email → Clicks "Request OTP"
6. OTP appears in popup modal
7. Clicks "Got it!" → Redirected to OTP verification
8. Enters OTP → Logged in

## Setup Steps

### Step 1: Update Database
Open MySQL Workbench and run:
```sql
USE priorityiq;

ALTER TABLE users 
ADD COLUMN phone VARCHAR(15) AFTER email,
ADD COLUMN role VARCHAR(50) AFTER phone,
ADD COLUMN age INT AFTER role,
ADD COLUMN gender VARCHAR(10) AFTER age;

ALTER TABLE users ADD UNIQUE KEY unique_phone (phone);
```

### Step 2: Restart Flask App
```bash
python app.py
```

### Step 3: Test Registration
1. Go to: http://127.0.0.1:5000/register
2. Fill all required fields (Name, Email, Phone)
3. Optional: Role, Age, Gender
4. Click "Register"
5. Success! Redirected to login

### Step 4: Test Login
1. Go to: http://127.0.0.1:5000/login
2. Enter registered email
3. Click "Request OTP"
4. OTP appears in popup
5. Click "Got it!"
6. Enter OTP on verification page
7. Success! Access dashboard

## API Endpoints

### New Endpoint
- `POST /api/auth/register` - Register new user

### Updated Endpoints
- `POST /api/auth/request_otp` - Now requires existing email
- `POST /api/auth/verify_otp` - Unchanged
- `GET /api/auth/status` - Now returns user name too

## Validation Rules

### Registration
- Name: Required, non-empty
- Email: Required, valid format, unique
- Phone: Required, 10+ digits, unique
- Role: Optional, dropdown selection
- Age: Optional, 13-120 range
- Gender: Optional, dropdown selection

### Login
- Email: Must be registered
- OTP: 6-digit number

## Features

### OTP Popup Modal
- Displays 6-digit OTP in large font
- Styled with blue background
- "Got it!" button to proceed
- Click outside to close
- Auto-redirects to verification

### Registration Form
- Clean, modern design
- Dropdown for Role and Gender
- Number input for Age
- Phone validation
- Real-time error messages
- Success message before redirect

## Security

- ✅ Email uniqueness check
- ✅ Phone uniqueness check
- ✅ Input validation (age range, phone format)
- ✅ Secure OTP generation
- ✅ Session management
- ✅ SQL injection prevention

## Troubleshooting

### Error: "Email already registered"
- User already exists, use login instead

### Error: "Phone number already registered"
- Phone is already in use, use different number

### Error: "Email not registered"
- User needs to register first

### OTP not showing
- Check browser console for errors
- Ensure JavaScript is enabled

## Next Steps

1. ✅ Update database schema
2. ✅ Test registration flow
3. ✅ Test login with OTP popup
4. ✅ Verify dashboard access

Your registration system is now complete! 🎉
