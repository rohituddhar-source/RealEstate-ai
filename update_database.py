# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 10:27:35 2026

@author: ROHIT
"""

# update_database.py
import sqlite3

def update_db():
    """Add first_name and last_name columns to users table"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Add missing columns if they don't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        print("✅ Added first_name column")
    except:
        print("first_name column already exists")
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
        print("✅ Added last_name column")
    except:
        print("last_name column already exists")
    
    conn.commit()
    conn.close()
    print("✅ Database update complete!")

if __name__ == "__main__":
    update_db()