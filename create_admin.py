import sqlite3
import bcrypt

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

email = "admin@demo.com"
password = "Admin@123"

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

cursor.execute(
    "INSERT INTO tbladminlogin (userid, password) VALUES (?, ?)",
    (email, hashed)
)

conn.commit()
conn.close()

print("Admin Created")
print("Email:", email)
print("Password:", password)
