from db_connection import get_db_connection

email = input("Enter email to make admin: ").strip()

conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("UPDATE users SET is_admin=TRUE WHERE email=%s", (email,))
conn.commit()

if cursor.rowcount > 0:
    print(f"[OK] {email} is now an admin!")
else:
    print(f"[ERROR] User {email} not found")

cursor.close()
conn.close()
