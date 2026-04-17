# utils/auth.py
import sqlite3
import bcrypt
from datetime import datetime
import os

def init_db():
    """Initialize the SQLite database with users table"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            logged_in INTEGER DEFAULT 0,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def add_user(username, email, first_name, last_name, password):
    """Add new user to database"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        c.execute('''
            INSERT INTO users (username, email, first_name, last_name, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, first_name, last_name, password_hash, datetime.now()))
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    finally:
        conn.close()

def get_user(username_or_email):
    """Get user by username or email"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM users WHERE username = ? OR email = ?
    ''', (username_or_email, username_or_email))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'first_name': user[3],
            'last_name': user[4],
            'password_hash': user[5],
            'failed_attempts': user[6],
            'logged_in': user[7],
            'last_login': user[8],
            'created_at': user[9]
        }
    return None

def update_login_status(username, status):
    """Update user login status and last login time"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET logged_in = ?, last_login = ?, failed_attempts = 0
        WHERE username = ?
    ''', (1 if status else 0, datetime.now(), username))
    
    conn.commit()
    conn.close()

def increment_failed_attempts(username):
    """Increment failed login attempts"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET failed_attempts = failed_attempts + 1
        WHERE username = ?
    ''', (username,))
    
    conn.commit()
    conn.close()

def reset_failed_attempts(username):
    """Reset failed login attempts"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET failed_attempts = 0
        WHERE username = ?
    ''', (username,))
    
    conn.commit()
    conn.close()

def get_all_users():
    """Get all registered users"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, username, email, first_name, last_name, created_at, last_login, logged_in
        FROM users ORDER BY created_at DESC
    ''')
    
    users = c.fetchall()
    conn.close()
    return users

# Initialize database
init_db()