# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 10:53:23 2026

@author: ROHIT
"""

# setup_database.py
import sqlite3

print("=" * 50)
print("Setting up database tables...")
print("=" * 50)

conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        password_hash TEXT,
        created_at TIMESTAMP,
        last_login TIMESTAMP,
        failed_attempts INTEGER DEFAULT 0,
        logged_in INTEGER DEFAULT 0,
        email_verified INTEGER DEFAULT 0
    )
''')
print("✅ Users table ready")

# Create OTP codes table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        otp_code TEXT,
        purpose TEXT,
        expires_at TEXT,
        used INTEGER DEFAULT 0
    )
''')
print("✅ OTP codes table ready")

conn.commit()
conn.close()

print("=" * 50)
print("✅ Database setup complete!")
print("=" * 50)