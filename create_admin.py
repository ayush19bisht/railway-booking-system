import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('railway.db')
c = conn.cursor()

name = "Admin"
email = "admin@example.com"
phone = "9999999999"
password = "admin123"  # You can change this if you want
hashed_pw = generate_password_hash(password)

# Add the admin user (is_admin = 1)
c.execute('''
    ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0
''')  # this will add the column if it's not there, may show warning once

conn.commit()

try:
    c.execute('''
        INSERT INTO users (name, email, phone, password, is_admin)
        VALUES (?, ?, ?, ?, 1)
    ''', (name, email, phone, hashed_pw))
    conn.commit()
    print("✅ Admin created successfully!")
except Exception as e:
    print("⚠️ Could not create admin:", e)

conn.close()
