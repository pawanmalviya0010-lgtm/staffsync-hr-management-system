"""Create the first administrator account. Run after importing schema.sql."""
import os
import getpass
import mysql.connector
from werkzeug.security import generate_password_hash

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "staffsync"),
)
name = input("Admin full name: ").strip() or "StaffSync Admin"
email = input("Admin email: ").strip().lower()
password = getpass.getpass("Admin password (minimum 8 characters): ")
if len(password) < 8:
    raise SystemExit("Password must be at least 8 characters.")
cur = conn.cursor()
cur.execute("SELECT id FROM users WHERE email=%s", (email,))
if cur.fetchone():
    raise SystemExit("That email already exists.")
cur.execute("INSERT INTO users(full_name,email,password_hash,role) VALUES(%s,%s,%s,'admin')",
            (name, email, generate_password_hash(password)))
conn.commit()
cur.close()
conn.close()
print("Admin created. Sign in at http://127.0.0.1:5000/login")
