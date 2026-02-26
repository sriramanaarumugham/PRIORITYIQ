from db_connection import get_db_connection

def setup_admin_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add is_admin column to users if not exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE")
        conn.commit()
        print("[OK] Added is_admin column")
    except:
        print("[OK] is_admin column already exists")

    # Admin credentials table (separate admin access list)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_credentials (
            admin_id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            dept_id INT AUTO_INCREMENT PRIMARY KEY,
            dept_name VARCHAR(100) UNIQUE NOT NULL,
            dept_code VARCHAR(10) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Exam schedules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_schedules (
            exam_id INT AUTO_INCREMENT PRIMARY KEY,
            dept_id INT NOT NULL,
            subject_name VARCHAR(200) NOT NULL,
            exam_date DATE NOT NULL,
            exam_time TIME NOT NULL,
            duration_mins INT NOT NULL,
            room_no VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE
        )
    """)
    
    # College events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS college_events (
            event_id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(200) NOT NULL,
            event_date DATE NOT NULL,
            event_time TIME,
            location VARCHAR(200),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            dept_id INT NOT NULL,
            attendance_date DATE NOT NULL,
            status ENUM('Present', 'Absent', 'Late') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE,
            UNIQUE KEY unique_attendance (user_id, attendance_date)
        )
    """)
    
    # Announcements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            announcement_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
            target_audience VARCHAR(50) DEFAULT 'All',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Insert default departments
    depts = [
        ('Computer Science', 'CSE'),
        ('Electronics', 'ECE'),
        ('Mechanical', 'MECH'),
        ('Civil', 'CIVIL'),
        ('Information Technology', 'IT')
    ]
    
    for name, code in depts:
        try:
            cursor.execute("INSERT INTO departments (dept_name, dept_code) VALUES (%s, %s)", (name, code))
        except:
            pass
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Admin tables created successfully")

if __name__ == "__main__":
    setup_admin_tables()
