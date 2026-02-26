# 🎓 Admin Panel - College Management Features

## Overview
The Admin Panel adds college management capabilities to PriorityIQ, allowing administrators to manage exam schedules, college events, attendance tracking, and announcements.

## Setup

### 1. Create Admin Tables
```bash
python setup_admin.py
```

This creates 5 new tables:
- `departments` - College departments (CSE, ECE, MECH, CIVIL, IT)
- `exam_schedules` - Exam schedules by department
- `college_events` - College-wide events
- `attendance` - Student attendance tracking
- `announcements` - Important announcements

### 2. Make User Admin
```bash
python make_admin.py
```
Enter the email of the user you want to make admin.

## Features

### 📝 Exam Schedules
- Add exams by department
- Specify subject, date, time, duration, and room
- Filter exams by department
- Delete exams

### 🎉 College Events
- Create college-wide events
- Set date, time, location, and description
- View all upcoming events
- Delete events

### ✅ Attendance Tracking
- Mark attendance for students
- Track Present/Absent/Late status
- View attendance records by user or department
- Automatic duplicate prevention (one record per user per day)

### 📢 Announcements
- Create announcements with priority levels (Low/Medium/High)
- Target specific audiences
- View all announcements chronologically
- Delete announcements

## Access Control

- Only users with `is_admin=TRUE` can access the admin panel
- Non-admin users see "Access Denied" message
- Admin link appears in navigation only for admin users

## Safety Features

✅ **Isolated Tables** - All admin features use separate tables, no modifications to existing tables
✅ **Backward Compatible** - Existing features continue working unchanged
✅ **Safe SQL** - Uses `IF NOT EXISTS` and parameterized queries
✅ **Optional Feature** - Can be completely ignored without affecting core functionality
✅ **Easy Rollback** - Can drop admin tables without affecting tasks/users

## API Endpoints

### Admin Check
- `GET /api/admin/check` - Check if current user is admin

### Departments
- `GET /api/admin/departments` - Get all departments

### Exams
- `POST /api/admin/exams/add` - Add exam schedule
- `GET /api/admin/exams/all` - Get all exams (optional ?dept_id filter)
- `DELETE /api/admin/exams/delete/<exam_id>` - Delete exam

### Events
- `POST /api/admin/events/add` - Add college event
- `GET /api/admin/events/all` - Get all events
- `DELETE /api/admin/events/delete/<event_id>` - Delete event

### Attendance
- `POST /api/admin/attendance/mark` - Mark attendance
- `GET /api/admin/attendance/all` - Get attendance records (optional ?user_id filter)

### Announcements
- `POST /api/admin/announcements/add` - Add announcement
- `GET /api/admin/announcements/all` - Get all announcements
- `DELETE /api/admin/announcements/delete/<announcement_id>` - Delete announcement

## Usage

1. Login to PriorityIQ
2. If you're an admin, you'll see "🎓 Admin" link in navigation
3. Click to access admin panel
4. Use tabs to switch between features:
   - 📝 Exam Schedules
   - 🎉 College Events
   - ✅ Attendance
   - 📢 Announcements

## Database Schema

```sql
-- Departments
CREATE TABLE departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) UNIQUE NOT NULL,
    dept_code VARCHAR(10) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exam Schedules
CREATE TABLE exam_schedules (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_id INT NOT NULL,
    subject_name VARCHAR(200) NOT NULL,
    exam_date DATE NOT NULL,
    exam_time TIME NOT NULL,
    duration_mins INT NOT NULL,
    room_no VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE
);

-- College Events
CREATE TABLE college_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME,
    location VARCHAR(200),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dept_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (user_id, attendance_date)
);

-- Announcements
CREATE TABLE announcements (
    announcement_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    target_audience VARCHAR(50) DEFAULT 'All',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Notes

- All forms support Enter key submission
- Tables are responsive and mobile-friendly
- Gradient UI matches PriorityIQ design language
- Real-time updates after add/delete operations
- No impact on existing 49+ features

## Total Features Now: 53+

✅ All previous 49+ features
✅ Exam schedule management
✅ College events management
✅ Attendance tracking
✅ Announcements system
