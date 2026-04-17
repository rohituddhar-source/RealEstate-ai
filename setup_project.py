# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 19:20:52 2026

@author: ROHIT
"""

# setup_project.py
import os

def setup_project():
    """Create all necessary folders and files for the project"""
    
    print("🚀 Setting up Real Estate AI Project...")
    
    # 1. Create utils folder
    if not os.path.exists('utils'):
        os.mkdir('utils')
        print("✅ Created 'utils' folder")
    else:
        print("✅ 'utils' folder already exists")
    
    # 2. Create __init__.py in utils
    init_file = os.path.join('utils', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# This file makes 'utils' a Python package\n")
        print("✅ Created utils/__init__.py")
    
    # 3. Create auth.py
    auth_file = os.path.join('utils', 'auth.py')
    if not os.path.exists(auth_file):
        with open(auth_file, 'w') as f:
            f.write('''# utils/auth.py
import hashlib
import json
import os
from datetime import datetime

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_db():
    """Initialize the users database file if it doesn't exist"""
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as f:
            json.dump({}, f)
        print("✅ Created users.json database")

def save_user(username, password):
    """Save a new user to the database"""
    with open('users.json', 'r') as f:
        users = json.load(f)
    
    users[username] = {
        'password': hash_password(password),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': None
    }
    
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    return True

def check_user(username, password):
    """Check if username and password are correct"""
    with open('users.json', 'r') as f:
        users = json.load(f)
    
    if username in users:
        return users[username]['password'] == hash_password(password)
    return False
''')
        print("✅ Created utils/auth.py")
    
    # 4. Create model.py (simplified version)
    model_file = os.path.join('utils', 'model.py')
    if not os.path.exists(model_file):
        with open(model_file, 'w') as f:
            f.write('''# utils/model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

def load_and_engineer_data():
    """Load and engineer features from data.csv"""
    df = pd.read_csv('data.csv')
    
    # Basic features
    df['price_per_sqft'] = df['rent'] / df['area']
    furnish_map = {'Furnished': 2, 'Semi-Furnished': 1, 'Unfurnished': 0}
    df['furnish_score'] = df['furnishing'].map(furnish_map)
    df['luxury_score'] = df['bathrooms'] + df['balconies'] + df['furnish_score']
    
    return df

def train_model(data):
    """Train Random Forest model on the data"""
    df_ml = pd.get_dummies(data, columns=['city', 'furnishing'], drop_first=True)
    feature_cols = [col for col in df_ml.columns if col not in 
                   ['rent', 'house_type', 'locality', 'price_per_sqft']]
    X = df_ml[feature_cols]
    y = df_ml['rent']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model, X.columns.tolist()
''')
        print("✅ Created utils/model.py")
    
    # 5. Create requirements.txt
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write('''streamlit
pandas
numpy
plotly
scikit-learn
fpdf
pillow''')
        print("✅ Created requirements.txt")
    
    # 6. Show final structure
    print("\n📁 Final Project Structure:")
    print("   📂 your_project_folder/")
    print("   ├── 📄 app.py (create this)")
    print("   ├── 📄 one.py (your file)")
    print("   ├── 📄 data.csv (your data)")
    print("   ├── 📄 requirements.txt")
    print("   ├── 📄 setup_project.py (this file)")
    print("   └── 📂 utils/")
    print("       ├── 📄 __init__.py")
    print("       ├── 📄 auth.py")
    print("       └── 📄 model.py")
    
    print("\n🎉 Setup complete! Now you can:")
    print("1. Create app.py in the main folder")
    print("2. Copy your dashboard code to app.py")
    print("3. Run: streamlit run app.py")

if __name__ == "__main__":
    setup_project()