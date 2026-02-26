-- Admin Features Schema for PriorityIQ
-- Run this in MySQL Workbench

USE priorityiq;

-- 1. Add admin role to existing users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);

-- 1b. Admin credentials table (separate admin access list)
CREATE TABLE IF NOT EXISTS admin_credentials (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Departments table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE,
    dept_code VARCHAR(20) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default departments
INSERT INTO departments (dept_name, dept_code) VALUES
('Computer Science', 'CSE'),
('Electronics', 'ECE'),
('Mechanical', 'MECH'),
('Civil', 'CIVIL'),
('Information Technology', 'IT')
ON DUPLICATE KEY UPDATE dept_name=dept_name;

-- 3. Exam Schedules table
CREATE TABLE IF NOT EXISTS exam_schedules (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_id INT NOT NULL,
    exam_name VARCHAR(200) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    exam_date DATE NOT NULL,
    exam_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    room_number VARCHAR(50),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 4. College Events table
CREATE TABLE IF NOT EXISTS college_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(200) NOT NULL,
    event_description TEXT,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    venue VARCHAR(200),
    event_type VARCHAR(50),
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 5. Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dept_id INT,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Late') NOT NULL,
    remarks TEXT,
    marked_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (marked_by) REFERENCES users(user_id),
    UNIQUE KEY unique_attendance (user_id, attendance_date)
);

-- 6. Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    announcement_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High', 'Urgent') DEFAULT 'Medium',
    target_audience ENUM('All', 'Students', 'Faculty', 'Department') DEFAULT 'All',
    dept_id INT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Create first admin user (CHANGE EMAIL AND DETAILS)
INSERT INTO users (name, email, phone, role, is_admin, password) 
VALUES ('College Admin', 'admin@college.edu', '9999999999', 'admin', TRUE, '')
ON DUPLICATE KEY UPDATE is_admin=TRUE;

-- Allow admin email in admin credentials
INSERT INTO admin_credentials (email, active)
VALUES ('admin@college.edu', TRUE)
ON DUPLICATE KEY UPDATE active=TRUE;

-- Indexes for better performance
CREATE INDEX idx_exam_date ON exam_schedules(exam_date);
CREATE INDEX idx_event_date ON college_events(event_date);
CREATE INDEX idx_attendance_date ON attendance(attendance_date);
CREATE INDEX idx_announcement_created ON announcements(created_at);
