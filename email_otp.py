# email_otp.py
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from datetime import datetime, timedelta
import bcrypt
import traceback

# ==================== YOUR GMAIL SETTINGS ====================
# ⚠️ IMPORTANT: Change these to YOUR Gmail and App Password
YOUR_GMAIL = "rohituddhar@gmail.com"  # <---- CHANGE THIS
YOUR_APP_PASSWORD = "fpwe muze zknv iaen"  # <---- CHANGE THIS (16 characters with spaces)
# =============================================================

def hash_password(password):
    """Hash password for security"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_otp():
    """Generate 6-digit OTP"""
    return f"{random.randint(100000, 999999):06d}"

def send_otp_email(email, otp, purpose="login"):
    """Send OTP email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = YOUR_GMAIL
        msg['To'] = email
        
        if purpose == "signup":
            msg['Subject'] = "📝 Verify Your Email - RealEstate AI Pro"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px; 
                            border: 1px solid #4f8df5; border-radius: 10px;">
                    <h2 style="color: #4f8df5;">🏙️ RealEstate AI Pro</h2>
                    <p>Welcome! Please verify your email address.</p>
                    <h1 style="font-size: 48px; color: #6c5ce7; letter-spacing: 5px;">{otp}</h1>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
            </body>
            </html>
            """
        else:
            msg['Subject'] = "🔐 Your Login Code - RealEstate AI Pro"
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 500px; margin: 0 auto; padding: 20px; 
                            border: 1px solid #4f8df5; border-radius: 10px;">
                    <h2 style="color: #4f8df5;">🏙️ RealEstate AI Pro</h2>
                    <p>Your login code is:</p>
                    <h1 style="font-size: 48px; color: #6c5ce7; letter-spacing: 5px;">{otp}</h1>
                    <p>This code will expire in <strong>5 minutes</strong>.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                </div>
            </body>
            </html>
            """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(YOUR_GMAIL, YOUR_APP_PASSWORD.replace(' ', ''))
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent to {email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        traceback.print_exc()
        return False

def save_otp(email, otp, purpose):
    """Save OTP to database"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
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
        
        # Delete old OTPs for this email and purpose
        cursor.execute("DELETE FROM otp_codes WHERE email = ? AND purpose = ?", (email, purpose))
        
        expires_at = datetime.now() + timedelta(minutes=10 if purpose == "signup" else 5)
        cursor.execute(
            "INSERT INTO otp_codes (email, otp_code, purpose, expires_at, used) VALUES (?, ?, ?, ?, ?)",
            (email, otp, purpose, expires_at.isoformat(), 0)
        )
        
        conn.commit()
        conn.close()
        print(f"✅ OTP saved for {email}: {otp} (purpose: {purpose})")
        return True
    except Exception as e:
        print(f"Save OTP error: {e}")
        traceback.print_exc()
        return False

def verify_otp(email, otp, purpose):
    """Verify OTP"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Get the latest OTP for this email and purpose
        cursor.execute('''
            SELECT otp_code, expires_at, used 
            FROM otp_codes 
            WHERE email = ? AND purpose = ? 
            ORDER BY expires_at DESC 
            LIMIT 1
        ''', (email, purpose))
        
        result = cursor.fetchone()
        
        if result:
            stored_otp, expires_at_str, used = result
            expires_at = datetime.fromisoformat(expires_at_str)
            current_time = datetime.now()
            
            print(f"DEBUG: Checking OTP for {email}")
            print(f"  Stored OTP: {stored_otp}")
            print(f"  User OTP: {otp}")
            print(f"  Expires at: {expires_at}")
            print(f"  Current time: {current_time}")
            print(f"  Used: {used}")
            
            if used == 0 and current_time < expires_at and stored_otp == otp:
                # Mark as used
                cursor.execute("UPDATE otp_codes SET used = 1 WHERE email = ? AND purpose = ?", (email, purpose))
                conn.commit()
                conn.close()
                print(f"✅ OTP verified successfully for {email}")
                return True
            else:
                if used == 1:
                    print("❌ OTP already used")
                if current_time >= expires_at:
                    print("❌ OTP expired")
                if stored_otp != otp:
                    print("❌ OTP mismatch")
        else:
            print(f"❌ No OTP found for {email} with purpose {purpose}")
        
        conn.close()
        return False
    except Exception as e:
        print(f"Verify OTP error: {e}")
        traceback.print_exc()
        return False

def create_user(email, password, first_name, last_name):
    """Create new user in database"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already registered"
        
        username = email.split('@')[0]
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, first_name, last_name, password_hash, created_at, email_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, first_name, last_name, password_hash, datetime.now().isoformat(), 0))
        
        conn.commit()
        conn.close()
        print(f"✅ User created: {email}")
        return True, "User created"
    except Exception as e:
        print(f"Create user error: {e}")
        traceback.print_exc()
        return False, f"Error: {e}"

def verify_email(email):
    """Mark email as verified"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email_verified = 1 WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        print(f"✅ Email verified: {email}")
        return True
    except Exception as e:
        print(f"Verify email error: {e}")
        return False

def is_email_verified(email):
    """Check if email is verified"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email_verified FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 1
    except:
        return False

def authenticate_user(email, password):
    """Check if user exists and password is correct"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, email_verified FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            password_hash, email_verified = result
            if verify_password(password, password_hash):
                return True, email_verified == 1
        return False, False
    except:
        return False, False

def get_user_by_email(email):
    """Get user details"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email, first_name, last_name, username, created_at FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'email': result[0],
                'first_name': result[1] or '',
                'last_name': result[2] or '',
                'username': result[3],
                'created_at': result[4]
            }
        return None
    except:
        return None

def update_last_login(email):
    """Update last login time"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = ?, logged_in = 1 WHERE email = ?", (datetime.now().isoformat(), email))
        conn.commit()
        conn.close()
    except:
        pass

def update_user_name(email, first_name, last_name):
    """Update user name"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET first_name = ?, last_name = ? WHERE email = ?", (first_name, last_name, email))
        conn.commit()
        conn.close()
    except:
        pass