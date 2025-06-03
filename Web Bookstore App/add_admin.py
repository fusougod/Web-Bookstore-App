import sqlite3
from werkzeug.security import generate_password_hash
import secrets
import os

# Path to the database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookstore.db')

# Connect to the database
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # New admin details
    username = 'admin_fusougod'  # Replace with your desired username
    password = '123password'  # Replace with your desired password
    admin_key = secrets.token_hex(16)  # Generate a unique admin key

    # Insert new admin account
    c.execute('INSERT OR IGNORE INTO admins (username, password, admin_key) VALUES (?, ?, ?)',
              (username, generate_password_hash(password), admin_key))
    conn.commit()
    print(f"Admin account created: Username = {username}, Admin Key = {admin_key}, Password = {password}")
except Exception as e:
    print(f"Error adding admin account: {e}")
finally:
    conn.close()