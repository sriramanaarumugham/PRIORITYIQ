from db_connection import get_db_connection

email = input("Enter admin email to allow: ").strip().lower()

if not email or "@" not in email:
    print("[ERROR] Valid email required")
    raise SystemExit(1)

conn = get_db_connection()
if not conn:
    print("[ERROR] Database connection failed")
    raise SystemExit(1)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_credentials (
        admin_id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute(
    "INSERT INTO admin_credentials (email, active) VALUES (%s, TRUE) "
    "ON DUPLICATE KEY UPDATE active=TRUE",
    (email,)
)

# Keep legacy is_admin in sync for compatibility
cursor.execute("UPDATE users SET is_admin=TRUE WHERE email=%s", (email,))

conn.commit()
cursor.close()
conn.close()

print(f"[OK] {email} is now allowed as admin")
