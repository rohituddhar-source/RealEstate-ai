# utils/model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import os
import re

def clean_numeric_column(series):
    """Extract numbers from text strings"""
    if series.dtype == 'object':
        # Extract numbers using regex
        return series.astype(str).apply(lambda x: float(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else np.nan)
    return series

def extract_city_from_text(text):
    """Extract city name from text"""
    text = str(text).lower()
    cities = ['mumbai', 'delhi', 'bangalore', 'bengaluru', 'chennai', 'pune', 
              'hyderabad', 'kolkata', 'ahmedabad', 'jaipur', 'noida', 'gurgaon']
    
    for city in cities:
        if city in text:
            return city.title()
    return 'Mumbai'  # Default

@st.cache_data
def load_and_engineer_data():
    """Load and engineer features from data.csv with proper cleaning"""
    try:
        if not os.path.exists('data.csv'):
            st.warning("⚠️ data.csv not found. Using sample data.")
            return create_sample_data()
        
        df = pd.read_csv('data.csv')
        
        # Clean column names
        df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
        
        # ========== CLEAN NUMERIC COLUMNS ==========
        numeric_cols = ['area', 'beds', 'bathrooms', 'balconies', 'rent', 'area_rate']
        
        for col in numeric_cols:
            if col in df.columns:
                # Extract numbers from text
                df[col] = df[col].astype(str).str.extract('(\d+\.?\d*)').astype(float)
        
        # ========== HANDLE MISSING VALUES ==========
        # Fill missing area with median
        if 'area' in df.columns:
            df['area'].fillna(df['area'].median(), inplace=True)
        else:
            df['area'] = 1000
        
        # Fill missing beds
        if 'beds' in df.columns:
            df['beds'].fillna(2, inplace=True)
        else:
            df['beds'] = 2
        
        # Fill missing bathrooms
        if 'bathrooms' in df.columns:
            df['bathrooms'].fillna(2, inplace=True)
        else:
            df['bathrooms'] = 2
        
        # Fill missing balconies
        if 'balconies' in df.columns:
            df['balconies'].fillna(1, inplace=True)
        else:
            df['balconies'] = 1
        
        # Fill missing rent
        if 'rent' in df.columns:
            df['rent'].fillna(df['rent'].median(), inplace=True)
        else:
            df['rent'] = df['area'] * 50
        
        # ========== CREATE CITY COLUMN ==========
        if 'city' not in df.columns:
            if 'locality' in df.columns:
                df['city'] = df['locality'].apply(extract_city_from_text)
            else:
                df['city'] = 'Mumbai'
        
        # ========== CREATE FURNISHING COLUMN ==========
        if 'furnishing' not in df.columns:
            df['furnishing'] = 'Semi-Furnished'
        
        # Standardize furnishing values
        furnishing_map = {
            'furnished': 'Furnished',
            'fully furnished': 'Furnished',
            'semi furnished': 'Semi-Furnished',
            'semi-furnished': 'Semi-Furnished',
            'unfurnished': 'Unfurnished',
            'not furnished': 'Unfurnished'
        }
        df['furnishing'] = df['furnishing'].astype(str).str.lower().map(
            furnishing_map).fillna('Semi-Furnished')
        
        # ========== CREATE AREA_RATE ==========
        if 'area_rate' not in df.columns:
            df['area_rate'] = df['rent'] / df['area']
        
        # ========== FEATURE ENGINEERING ==========
        # Price per sqft
        df['price_per_sqft'] = df['rent'] / df['area']
        
        # Furnish score
        furnish_score_map = {'Furnished': 2, 'Semi-Furnished': 1, 'Unfurnished': 0}
        df['furnish_score'] = df['furnishing'].map(furnish_score_map).fillna(1)
        
        # Luxury score
        df['luxury_score'] = df['bathrooms'] + df['balconies'] + df['furnish_score']
        
        # Premium area flag
        city_avg = df.groupby('city')['area_rate'].transform('mean')
        df['is_premium_area'] = (df['area_rate'] > city_avg).astype(int)
        
        # Remove outliers for better predictions
        Q1 = df['rent'].quantile(0.25)
        Q3 = df['rent'].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df['rent'] >= Q1 - 1.5*IQR) & (df['rent'] <= Q3 + 1.5*IQR)]
        
        # Ensure all numeric columns are float
        for col in ['area', 'beds', 'bathrooms', 'balconies', 'rent', 'area_rate', 'price_per_sqft', 'luxury_score', 'is_premium_area']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop any remaining NaN values
        df = df.dropna()
        
        st.success(f"✅ Loaded {len(df)} properties after cleaning")
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return create_sample_data()

def create_sample_data():
    """Create sample data for demonstration"""
    np.random.seed(42)
    
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad']
    furnishing = ['Furnished', 'Semi-Furnished', 'Unfurnished']
    
    data = []
    for _ in range(200):
        city = np.random.choice(cities)
        area = np.random.randint(400, 2500)
        beds = np.random.randint(1, 5)
        bathrooms = np.random.randint(1, 4)
        balconies = np.random.randint(0, 3)
        furn = np.random.choice(furnishing)
        
        # Calculate rent based on features
        base_rate = 40
        city_factors = {'Mumbai': 1.5, 'Delhi': 1.4, 'Bangalore': 1.3, 
                       'Chennai': 1.1, 'Pune': 1.2, 'Hyderabad': 1.0}
        base_rate *= city_factors.get(city, 1.0)
        
        if furn == 'Furnished':
            base_rate *= 1.3
        elif furn == 'Semi-Furnished':
            base_rate *= 1.1
        
        rent = area * base_rate * np.random.uniform(0.8, 1.2)
        
        data.append({
            'city': city,
            'area': area,
            'beds': beds,
            'bathrooms': bathrooms,
            'balconies': balconies,
            'furnishing': furn,
            'area_rate': base_rate,
            'rent': int(rent)
        })
    
    df = pd.DataFrame(data)
    df['price_per_sqft'] = df['rent'] / df['area']
    df['furnish_score'] = df['furnishing'].map({'Furnished':2, 'Semi-Furnished':1, 'Unfurnished':0})
    df['luxury_score'] = df['bathrooms'] + df['balconies'] + df['furnish_score']
    df['is_premium_area'] = 0
    
    return df

@st.cache_resource
def train_model(data):
    """Train Random Forest model"""
    if data is None or data.empty:
        return None, [], None
    
    try:
        # Select only numeric columns for features
        numeric_cols = ['area', 'beds', 'bathrooms', 'balconies', 'area_rate', 
                       'price_per_sqft', 'luxury_score', 'is_premium_area']
        
        # Create dummy variables for categorical columns
        categorical_cols = []
        if 'city' in data.columns:
            categorical_cols.append('city')
        if 'furnishing' in data.columns:
            categorical_cols.append('furnishing')
        
        if categorical_cols:
            df_encoded = pd.get_dummies(data, columns=categorical_cols, drop_first=True)
        else:
            df_encoded = data.copy()
        
        # Select feature columns (all numeric + dummies)
        feature_cols = [col for col in df_encoded.columns if col != 'rent']
        
        X = df_encoded[feature_cols]
        y = data['rent']
        
        # Ensure all columns are numeric
        X = X.apply(pd.to_numeric, errors='coerce')
        X = X.fillna(0)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X, y)
        
        # Feature importance
        importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return model, feature_cols, importance_df
    except Exception as e:
        st.error(f"Error training model: {e}")
        return None, [], None

def create_input_row(area, beds, baths, balc, city, furn, rate, df, model_columns):
    """Create model input row from user selections"""
    try:
        row = pd.DataFrame([[area, beds, baths, balc, rate]], 
                           columns=['area', 'beds', 'bathrooms', 'balconies', 'area_rate'])
        
        f_val = 2 if furn == 'Furnished' else 1 if furn == 'Semi-Furnished' else 0
        row['luxury_score'] = baths + balc + f_val
        
        city_data = df[df['city'] == city]
        city_avg_val = city_data['area_rate'].mean() if len(city_data) > 0 else rate
        row['is_premium_area'] = 1 if rate > city_avg_val else 0
        
        row['price_per_sqft'] = rate
        
        for col in model_columns:
            if col not in row.columns:
                if col.startswith('city_'):
                    row[col] = 1 if f"city_{city}" == col else 0
                elif col.startswith('furnishing_'):
                    row[col] = 1 if f"furnishing_{furn}" == col else 0
                else:
                    row[col] = 0
        
        return row[model_columns]
    except Exception as e:
        st.error(f"Error creating input row: {e}")
        return None

def get_market_sentiment(city, df):
    """Get market sentiment for a city"""
    try:
        city_data = df[df['city'] == city]
        if len(city_data) == 0:
            return "📊 Unknown", "Insufficient data"
        
        overall_avg = df['rent'].mean()
        city_avg = city_data['rent'].mean()
        
        if city_avg > overall_avg * 1.2:
            return "🔥 Hot Market", f"+{((city_avg/overall_avg)-1)*100:.0f}% above avg"
        elif city_avg > overall_avg:
            return "📈 Growing", f"+{((city_avg/overall_avg)-1)*100:.0f}% above avg"
        elif city_avg > overall_avg * 0.8:
            return "📊 Stable", f"{((city_avg/overall_avg)-1)*100:.0f}% vs avg"
        else:
            return "💰 Value Market", f"{((1 - city_avg/overall_avg)*100):.0f}% below avg"
    except:
        return "📊 Unknown", "Data unavailable"