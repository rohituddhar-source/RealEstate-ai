# -*- coding: utf-8 -*-
"""
database.py - Secure user authentication for RealEstate AI Pro
Created on Mon Mar 16 19:44:44 2026
@author: ROHIT
"""

import sqlite3
import bcrypt
from datetime import datetime
import os

def init_db():
    """Initialize the SQLite database with users table"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Create users table with all 10 columns
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
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

def hash_password(password):
    """Hash password using bcrypt"""
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception as e:
        print(f"❌ Error hashing password: {e}")
        return None

def verify_password(password, hashed):
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"❌ Error verifying password: {e}")
        return False

def add_user(username, email, first_name, last_name, password):
    """Add new user to database"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Check if user already exists
        c.execute("SELECT username FROM users WHERE username = ? OR email = ?", 
                 (username, email))
        if c.fetchone():
            return False, "Username or email already exists"
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            return False, "Error creating password hash"
        
        # Insert new user
        c.execute('''
            INSERT INTO users 
            (username, email, first_name, last_name, password_hash, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, first_name, last_name, password_hash, datetime.now()))
        
        conn.commit()
        return True, "User created successfully"
        
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()

def get_user(username_or_email):
    """Get user by username or email"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM users WHERE username = ? OR email = ?
        ''', (username_or_email, username_or_email))
        
        user = c.fetchone()
        
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
        
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_login_status(username, status):
    """Update user login status and last login time"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET logged_in = ?, last_login = ?, failed_attempts = 0
            WHERE username = ?
        ''', (1 if status else 0, datetime.now(), username))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error updating login status: {e}")
        return False
    finally:
        if conn:
            conn.close()

def increment_failed_attempts(username):
    """Increment failed login attempts"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET failed_attempts = failed_attempts + 1
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error incrementing failed attempts: {e}")
        return False
    finally:
        if conn:
            conn.close()

def reset_failed_attempts(username):
    """Reset failed login attempts"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET failed_attempts = 0
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error resetting failed attempts: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_all_users():
    """Get all users (for admin purposes)"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('''
            SELECT username, email, first_name, last_name, logged_in, 
                   last_login, created_at, failed_attempts 
            FROM users
        ''')
        
        users = c.fetchall()
        return users
        
    except Exception as e:
        print(f"❌ Error getting all users: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_user(username):
    """Delete a user (for admin purposes)"""
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        
        return c.rowcount > 0
        
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_database():
    """Check if database exists and has correct structure"""
    try:
        if not os.path.exists('users.db'):
            print("❌ Database file not found")
            return False
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Check if users table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not c.fetchone():
            print("❌ Users table not found")
            return False
            
        # Check table structure
        c.execute("PRAGMA table_info(users)")
        columns = c.fetchall()
        print(f"✅ Database has {len(columns)} columns")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

# Initialize database on import
if __name__ != "__main__":
    # Only initialize when imported, not when run directly
    init_db()
    check_database()

# If run directly, show database info
if __name__ == "__main__":
    print("=" * 50)
    print("🔧 RealEstate AI Pro - Database Utility")
    print("=" * 50)
    
    init_db()
    
    if check_database():
        print("\n📊 Current Users:")
        users = get_all_users()
        if users:
            for user in users:
                print(f"   • {user[0]} ({user[1]}) - Logged in: {'Yes' if user[4] else 'No'}")
        else:
            print("   No users found")
    else:
        print("❌ Database check failed")