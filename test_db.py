import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

print("=== Testing Database Connection ===")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_PORT: {os.getenv('DB_PORT')}")
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"Password loaded: {'Yes' if os.getenv('DB_PASSWORD') else 'No'}")

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "priorityiq")
    )
    print("\n✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
