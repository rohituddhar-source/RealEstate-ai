# app.py

import streamlit as st
from email_otp import (
    send_otp_email, save_otp, verify_otp, create_user, verify_email,
    authenticate_user, get_user_by_email, update_last_login, is_email_verified
)
from utils.model import (
    load_and_engineer_data, 
    train_model, 
    create_input_row, 
    get_market_sentiment
)
from utils.reports import create_comprehensive_report
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import numpy as np
from datetime import datetime
import random

# Page config
st.set_page_config(
    page_title="RealEstate AI Pro",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DARK THEME CSS ====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); }
    .main .block-container { background: rgba(15, 25, 35, 0.95); border-radius: 24px; padding: 2rem; margin: 1rem; border: 1px solid rgba(79, 141, 245, 0.2); }
    .stMarkdown, .stText, p, h1, h2, h3, label { color: #ffffff !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0a0a 0%, #0f0f1a 100%); border-right: 1px solid rgba(79, 141, 245, 0.2); }
    .stSelectbox div[data-baseweb="select"], .stNumberInput input { background: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(79, 141, 245, 0.3) !important; border-radius: 12px !important; color: white !important; }
    div[data-testid="metric-container"] { background: linear-gradient(135deg, rgba(26, 26, 46, 0.8), rgba(15, 25, 35, 0.8)); border: 1px solid rgba(79, 141, 245, 0.2); border-radius: 16px; }
    .stButton button { background: linear-gradient(135deg, #4f8df5, #6c5ce7); border: none; border-radius: 40px; transition: all 0.3s; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(79, 141, 245, 0.5); }
    .auth-container { max-width: 500px; margin: 50px auto; padding: 40px; background: linear-gradient(135deg, #1a1a2e, #0f1923); border-radius: 24px; border: 1px solid rgba(79, 141, 245, 0.3); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }
    
    .stat-card {
        background: #0f172a;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid #334155;
        transition: transform 0.2s;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        border-color: #4f8df5;
    }
    .prediction-item {
        background: #1e293b;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #4f8df5;
    }
    .alert-item {
        background: #0f172a;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #334155;
    }
    .favorite-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border-radius: 16px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 3px solid #f59e0b;
    }
    .deal-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 4px solid;
        transition: transform 0.2s;
    }
    .deal-card:hover {
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'auth_stage' not in st.session_state:
    st.session_state.auth_stage = "login"
if 'temp_email' not in st.session_state:
    st.session_state.temp_email = None
if 'temp_password' not in st.session_state:
    st.session_state.temp_password = None
if 'temp_name' not in st.session_state:
    st.session_state.temp_name = None
if 'prediction_history' not in st.session_state:
    st.session_state.prediction_history = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'comparison_history' not in st.session_state:
    st.session_state.comparison_history = []
if 'base_pred' not in st.session_state:
    st.session_state.base_pred = None
if 'last_prediction' not in st.session_state:
    st.session_state.last_prediction = None
if 'current_property' not in st.session_state:
    st.session_state.current_property = {}
if 'model_loaded' not in st.session_state:
    st.session_state.model_loaded = False
if 'df_data' not in st.session_state:
    st.session_state.df_data = None
if 'model_instance' not in st.session_state:
    st.session_state.model_instance = None
if 'model_features' not in st.session_state:
    st.session_state.model_features = None
if 'importance_df' not in st.session_state:
    st.session_state.importance_df = None

# ==================== AUTHENTICATION UI ====================
if not st.session_state.logged_in:
    
    if st.session_state.auth_stage == "login":
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/real-estate.png", width=80)
        st.markdown("<h1 style='text-align: center;'>🏙️ RealEstate AI Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Sign in to your account</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Create Account"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if email and password:
                        with st.spinner("🔐 Authenticating..."):
                            time.sleep(0.5)
                            valid, is_verified = authenticate_user(email, password)
                            
                            if valid:
                                if is_verified:
                                    user = get_user_by_email(email)
                                    st.session_state.user_data = user
                                    st.session_state.logged_in = True
                                    update_last_login(email)
                                    st.success("✅ Login successful! Redirecting...")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Please verify your email first. Check your inbox.")
                            else:
                                st.error("❌ Invalid email or password")
                    else:
                        st.warning("Please enter email and password")
        
        with tab2:
            with st.form("signup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input("First Name", placeholder="John")
                with col2:
                    last_name = st.text_input("Last Name", placeholder="Doe")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="•••••••• (min 6 characters)")
                confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    if not all([first_name, last_name, email, password]):
                        st.error("❌ Please fill all fields")
                    elif password != confirm:
                        st.error("❌ Passwords don't match")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        with st.spinner("📝 Creating your account..."):
                            time.sleep(0.5)
                            success, msg = create_user(email, password, first_name, last_name)
                        
                        if success:
                            with st.spinner("📧 Sending verification code..."):
                                time.sleep(0.5)
                                otp = random.randint(100000, 999999)
                                otp_str = f"{otp:06d}"
                                email_sent = send_otp_email(email, otp_str, "signup")
                                
                                if email_sent:
                                    save_otp(email, otp_str, "signup")
                                    st.session_state.temp_email = email
                                    st.session_state.temp_password = password
                                    st.session_state.temp_name = f"{first_name} {last_name}"
                                    st.session_state.auth_stage = "verify_signup"
                                    st.success(f"✅ Verification code sent to {email}")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to send verification email")
                        else:
                            st.error(f"❌ {msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.auth_stage == "verify_signup":
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.image("https://img.icons8.com/fluency/96/real-estate.png", width=80)
        st.markdown("<h1 style='text-align: center;'>📧 Verify Your Email</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Enter the code sent to {st.session_state.temp_email}</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.info("📌 The verification code expires in **10 minutes**. Check your spam folder if needed.")
        
        otp = st.text_input("Enter 6-digit verification code", type="password", placeholder="123456", key="otp_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verify & Continue", key="verify_btn", use_container_width=True):
                if otp:
                    with st.spinner("🔐 Verifying code..."):
                        time.sleep(0.5)
                        if verify_otp(st.session_state.temp_email, otp, "signup"):
                            with st.spinner("✨ Setting up your account..."):
                                verify_email(st.session_state.temp_email)
                                time.sleep(0.5)
                                
                                user = get_user_by_email(st.session_state.temp_email)
                                st.session_state.user_data = user
                                st.session_state.logged_in = True
                                update_last_login(st.session_state.temp_email)
                                st.session_state.auth_stage = "login"
                                st.session_state.temp_email = None
                                
                                st.success("✅ Email verified successfully! Welcome to RealEstate AI Pro!")
                                time.sleep(2)
                                st.rerun()
                        else:
                            st.error("❌ Invalid or expired code. Please try again.")
                else:
                    st.warning("⚠️ Please enter the verification code")
        
        with col2:
            if st.button("🔄 Resend Code", key="resend_btn", use_container_width=True):
                with st.spinner("📧 Sending new code..."):
                    time.sleep(0.5)
                    new_otp = random.randint(100000, 999999)
                    new_otp_str = f"{new_otp:06d}"
                    if send_otp_email(st.session_state.temp_email, new_otp_str, "signup"):
                        save_otp(st.session_state.temp_email, new_otp_str, "signup")
                        st.success("✅ New code sent! Check your email.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to send. Please try again.")
        
        with st.expander("💡 Didn't receive the code?"):
            st.markdown("""
            - Check your **spam/junk folder**
            - Verify you entered the correct email address
            - Wait 30 seconds and click **Resend Code**
            - Ensure your email provider accepts automated emails
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ==================== MAIN APP (RUNS AFTER LOGIN) ====================

# FIX: Check if user_data exists
if st.session_state.user_data is None:
    st.error("User data not found. Please login again.")
    st.stop()

user = st.session_state.user_data
full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
if not full_name:
    full_name = user.get('username', 'User')

# ==================== LOAD DATA AND MODEL ====================
if not st.session_state.model_loaded:
    with st.spinner("🚀 Loading market data and training AI model..."):
        df = load_and_engineer_data()
        if df is not None and not df.empty:
            model, features, importance_df = train_model(df)
            if model is not None:
                st.session_state.df_data = df
                st.session_state.model_instance = model
                st.session_state.model_features = features
                st.session_state.importance_df = importance_df
                st.session_state.model_loaded = True

df = st.session_state.df_data
model = st.session_state.model_instance
features = st.session_state.model_features
importance_df = st.session_state.importance_df

if df is None or model is None:
    st.error("Unable to load data. Please check your data file.")
    st.stop()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/real-estate.png", width=50)
    st.markdown("## 🏙️ RealEstate AI")
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4f8df5, #6c5ce7); 
                    border-radius: 50%; margin: 0 auto 0.5rem auto; display: flex; align-items: center; 
                    justify-content: center;">
            <span style="font-size: 1.5rem;">👤</span>
        </div>
        <p style="color: white; margin: 0;"><strong>{full_name}</strong></p>
        <p style="color: #94a3b8; font-size: 12px;">{user.get('email', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🏠 Property Details")
    
    city = st.selectbox("📍 City", df['city'].unique())
    area = st.number_input("📐 Area (sqft)", 300, 5000, 1200, help="Typical range: 300-5000 sqft")
    beds = st.slider("🛏️ Bedrooms", 1, 5, 2)
    baths = st.slider("🚽 Bathrooms", 1, 5, 2)
    balc = st.slider("🌅 Balconies", 0, 3, 1)
    furn = st.selectbox("🪑 Furnishing", df['furnishing'].unique())
    
    
    # Price Alert Section
    with st.expander("🔔 Set Price Alert"):
        alert_price = st.number_input("Alert at (₹)", value=int(df['rent'].median()))
        if st.button("➕ Set Alert", key="set_alert_sidebar"):
            st.session_state.alerts.append({
                'target': alert_price,
                'city': city,
                'created': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.toast("✅ Alert set successfully!", icon="🔔")
    
    st.markdown("---")
    if st.button("🚀 Predict Rent", key="predict_rent_btn", type="primary", use_container_width=True):
        with st.spinner("AI analyzing market data..."):
            time.sleep(1)
            input_row = create_input_row(area, beds, baths, balc, city, furn, df['area_rate'].mean(), df, features)
            if input_row is not None:
                prediction = model.predict(input_row)[0]
                st.session_state.base_pred = prediction
                st.session_state.last_prediction = prediction
                st.session_state.current_property = {
                    'city': city, 'area': area, 'beds': beds, 'baths': baths,
                    'balconies': balc, 'furnishing': furn, 'rent': prediction
                }
                st.session_state.prediction_history.append({
                    'rent': prediction, 'city': city, 'area': area,
                    'beds': beds, 'baths': baths, 'balconies': balc,
                    'furnishing': furn,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.toast(f"✅ Estimated Rent: ₹{prediction:,.0f}/month", icon="🎉")
    
    if st.session_state.base_pred:
        city_avg = df[df['city'] == city]['rent'].mean()
        diff = ((st.session_state.base_pred - city_avg) / city_avg) * 100 if city_avg > 0 else 0
        st.metric("💰 Current Rent", f"₹{st.session_state.base_pred:,.0f}")
        if abs(diff) < 5:
            st.caption("📊 At market rate")
        elif diff > 0:
            st.caption(f"📈 {diff:.1f}% above market")
        else:
            st.caption(f"📉 {abs(diff):.1f}% below market")
    
    st.markdown("---")
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.session_state.base_pred = None
        st.rerun()

# ==================== MAIN TABS ====================
st.title("🏙️ Real Estate Intelligence Dashboard")
st.markdown(f"Welcome back, **{full_name}**! 👋")

# Create 8 tabs (added Favorites tab)
tabs = st.tabs(["📊 Market", "⚖️ Compare", "🧠 What-If", "💰 Investment", "🎯 Deals", "🤝 Negotiate", "⭐ Favorites", "👤 Profile"])

# ==================== TAB 0: MARKET INTELLIGENCE ====================
with tabs[0]:
    st.subheader("📊 Market Intelligence Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Properties", len(df))
    with col2: st.metric("Average Rent", f"₹{df['rent'].mean():,.0f}")
    with col3: st.metric("Avg Price/sqft", f"₹{df['price_per_sqft'].mean():,.0f}")
    with col4: st.metric("Cities Covered", len(df['city'].unique()))
    
    st.markdown("---")
    
    sentiment, trend = get_market_sentiment(city, df)
    st.info(f"📈 **{city} Market:** {sentiment} - {trend}")
    
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.box(df, x='city', y='rent', color='city', title="🏘️ Rent Distribution by City", template='plotly_dark')
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.scatter(df, x='area', y='rent', color='luxury_score', 
                         size='bathrooms', hover_data=['city', 'furnishing'],
                         title="📏 Area vs Rent Analysis", template='plotly_dark')
        st.plotly_chart(fig2, use_container_width=True)
    
    # City Ranking
    st.subheader("🏆 City Price Ranking")
    city_ranking = df.groupby('city')['rent'].mean().sort_values().reset_index()
    city_ranking.columns = ['City', 'Average Rent']
    max_rent = city_ranking['Average Rent'].max()
    for _, row in city_ranking.iterrows():
        percentage = (row['Average Rent'] / max_rent) * 100
        st.progress(percentage / 100, text=f"{row['City']}: ₹{row['Average Rent']:,.0f}")
    
    if importance_df is not None:
        st.subheader("🔑 Key Factors Influencing Rent")
        fig3 = px.bar(importance_df.head(10), x='importance', y='feature',
                     orientation='h', title="Top 10 Features Affecting Rent", template='plotly_dark')
        st.plotly_chart(fig3, use_container_width=True)

# ==================== TAB 1: SMART COMPARE ====================
with tabs[1]:
    st.subheader("⚖️ Smart Property Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏠 Property A")
        city1 = st.selectbox("City", df['city'].unique(), key='city1')
        area1 = st.number_input("Area (sqft)", 300, 5000, 1000, key='area1')
        beds1 = st.slider("Beds", 1, 5, 2, key='beds1')
        baths1 = st.slider("Baths", 1, 5, 2, key='baths1')
        balc1 = st.slider("Balconies", 0, 3, 1, key='balc1')
        furn1 = st.selectbox("Furnishing", df['furnishing'].unique(), key='furn1')
        
        inp1 = create_input_row(area1, beds1, baths1, balc1, city1, furn1, df['area_rate'].mean(), df, features)
        rent1 = model.predict(inp1)[0] if inp1 is not None else 0
        value1 = rent1 / area1 if area1 > 0 else 0
        
        st.metric("💰 Estimated Rent", f"₹{rent1:,.0f}")
        st.metric("📐 Price per sqft", f"₹{value1:.0f}")
    
    with col2:
        st.markdown("### 🏠 Property B")
        city2 = st.selectbox("City", df['city'].unique(), key='city2')
        area2 = st.number_input("Area (sqft)", 300, 5000, 1200, key='area2')
        beds2 = st.slider("Beds", 1, 5, 3, key='beds2')
        baths2 = st.slider("Baths", 1, 5, 2, key='baths2')
        balc2 = st.slider("Balconies", 0, 3, 1, key='balc2')
        furn2 = st.selectbox("Furnishing", df['furnishing'].unique(), key='furn2')
        
        inp2 = create_input_row(area2, beds2, baths2, balc2, city2, furn2, df['area_rate'].mean(), df, features)
        rent2 = model.predict(inp2)[0] if inp2 is not None else 0
        value2 = rent2 / area2 if area2 > 0 else 0
        
        st.metric("💰 Estimated Rent", f"₹{rent2:,.0f}")
        st.metric("📐 Price per sqft", f"₹{value2:.0f}")
    
    if rent1 > 0 and rent2 > 0:
        diff = ((rent2 - rent1) / rent1) * 100
        better_value = "A" if value1 < value2 else "B"
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price Difference", f"{abs(diff):.1f}%", delta=f"{'More' if diff > 0 else 'Less'}")
        with col2:
            st.metric("Better Value", f"Property {better_value}")
        with col3:
            st.metric("Savings Potential", f"₹{abs(rent1 - rent2):,.0f}/month")
        
        # Radar Chart Comparison
        categories = ['Rent Value', 'Price/sqft', 'Area', 'Location Value']
        scores1 = [100 - (rent1/rent2*100 if rent2>rent1 else 100), 
                   100 - (value1/value2*100 if value2>value1 else 100), 
                   (area1/area2*100 if area1<area2 else 100), 70]
        scores2 = [100 - (rent2/rent1*100 if rent1>rent2 else 100),
                   100 - (value2/value1*100 if value1>value2 else 100),
                   (area2/area1*100 if area2<area1 else 100), 70]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=scores1, theta=categories, fill='toself', name='Property A'))
        fig.add_trace(go.Scatterpolar(r=scores2, theta=categories, fill='toself', name='Property B'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), 
                         showlegend=True, template='plotly_dark', title="Feature Comparison")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("💾 Save This Comparison", key="save_compare"):
            st.session_state.comparison_history.append({
                'property_a': {'city': city1, 'area': area1, 'rent': rent1},
                'property_b': {'city': city2, 'area': area2, 'rent': rent2},
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.toast("Comparison saved to history!", icon="💾")

# ==================== TAB 2: WHAT-IF ANALYZER ====================
with tabs[2]:
    st.subheader("🧠 What-If Analyzer")
    
    if not st.session_state.base_pred:
        st.warning("⚠️ Make a prediction first using the sidebar")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 Modifications")
            extra_beds = st.slider("➕ Add Bedrooms", 0, 2, 0, help="Cost: ₹5,00,000 per bedroom")
            extra_baths = st.slider("🚽 Add Bathrooms", 0, 2, 0, help="Cost: ₹3,00,000 per bathroom")
            extra_balc = st.slider("🌅 Add Balconies", 0, 2, 0, help="Cost: ₹1,50,000 per balcony")
            upgrade_furn = st.checkbox("⬆️ Upgrade Furnishing", help="Cost: ₹2,00,000 - ₹3,00,000")
            premium_loc = st.checkbox("⭐ Premium Locality", help="Increases property value by 15-20%")
            
            sim_beds = beds + extra_beds
            sim_baths = baths + extra_baths
            sim_balc = balc + extra_balc
            sim_furn = 'Furnished' if upgrade_furn and furn != 'Furnished' else furn
            
            cost = (extra_beds * 500000) + (extra_baths * 300000) + (extra_balc * 150000)
            if upgrade_furn:
                if furn == 'Unfurnished':
                    cost += 200000
                elif furn == 'Semi-Furnished':
                    cost += 300000
            
            input_row = create_input_row(area, sim_beds, sim_baths, sim_balc, city, sim_furn, 
                                         df['area_rate'].mean(), df, features)
            sim_rent = model.predict(input_row)[0] if input_row is not None else st.session_state.base_pred
            if premium_loc:
                sim_rent *= 1.18
            rent_diff = sim_rent - st.session_state.base_pred
        
        with col2:
            st.markdown("### 📊 Impact Analysis")
            st.metric("Current Rent", f"₹{st.session_state.base_pred:,.0f}")
            st.metric("New Rent", f"₹{sim_rent:,.0f}", delta=f"₹{rent_diff:,.0f}")
            
            if cost > 0 and rent_diff > 0:
                months_to_recover = cost / rent_diff
                years_to_recover = months_to_recover / 12
                st.metric("Payback Period", f"{months_to_recover:.0f} months ({years_to_recover:.1f} years)")
                
                if months_to_recover < 24:
                    st.success("✅ Excellent ROI! Worth the investment")
                elif months_to_recover < 48:
                    st.info("📊 Good ROI - Consider if staying long-term")
                else:
                    st.warning("⚠️ Long payback period - Consider alternatives")
        
        st.markdown("---")
        st.subheader("📊 Multiple Scenarios Comparison")
        
        scenarios = {
            'Current': st.session_state.base_pred,
            '+1 Bedroom': st.session_state.base_pred * 1.10,
            '+1 Bathroom': st.session_state.base_pred * 1.05,
            'Fully Furnished': st.session_state.base_pred * 1.15,
            'Premium Location': st.session_state.base_pred * 1.18,
            'All Upgrades': st.session_state.base_pred * 1.35
        }
        
        scenario_df = pd.DataFrame(list(scenarios.items()), columns=['Scenario', 'Estimated Rent'])
        fig = px.bar(scenario_df, x='Scenario', y='Estimated Rent', color='Scenario',
                     title="Rent Comparison Across Scenarios", text_auto='.2s',
                     template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 3: INVESTMENT ====================
with tabs[3]:
    st.subheader("💰 Investment Calculator")
    
    current_rent = st.session_state.base_pred or df['rent'].median()
    
    col1, col2 = st.columns(2)
    
    with col1:
        purchase_price = st.number_input("🏠 Purchase Price (₹)", 
                                        value=int(current_rent * 200),
                                        step=100000,
                                        help="Total cost of the property")
        down_payment_pct = st.slider("💵 Down Payment %", 10, 50, 20)
        interest_rate = st.slider("📉 Interest Rate %", 6.0, 12.0, 8.5)
        loan_years = st.slider("⏱️ Loan Years", 5, 30, 20)
        maintenance = st.number_input("🔧 Monthly Maintenance (₹)", 1000, 10000, 3000)
        vacancy_rate = st.slider("📊 Vacancy Rate %", 0, 20, 5, help="Expected months without tenant")
        appreciation_rate = st.slider("📈 Annual Appreciation %", 0, 15, 5, help="Expected yearly value increase")
    
    with col2:
        down_amount = purchase_price * (down_payment_pct / 100)
        loan_amount = purchase_price - down_amount
        monthly_rate = interest_rate / 12 / 100
        months = loan_years * 12
        
        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
        else:
            emi = loan_amount / months
        
        annual_rent = current_rent * 12 * (1 - vacancy_rate/100)
        annual_maintenance = maintenance * 12
        net_income = annual_rent - annual_maintenance
        annual_loan_payment = emi * 12
        cash_flow = net_income - annual_loan_payment
        roi = (net_income / down_amount) * 100 if down_amount > 0 else 0
        cap_rate = (net_income / purchase_price) * 100
        
        st.metric("💰 Monthly EMI", f"₹{emi:,.0f}")
        st.metric("📈 Cash-on-Cash ROI", f"{roi:.1f}%")
        st.metric("🏦 Cap Rate", f"{cap_rate:.1f}%")
        st.metric("💵 Monthly Cash Flow", f"₹{cash_flow/12:,.0f}")
        
        if cash_flow > 0 and roi > 12:
            st.success("🌟 **A+ Grade** - Excellent Investment!")
        elif cash_flow > 0 and roi > 8:
            st.success("✅ **A Grade** - Good Investment")
        elif cash_flow > 0:
            st.info("📊 **B Grade** - Moderate Investment")
        else:
            st.error("❌ **C Grade** - Poor Investment")
    
    st.markdown("---")
    st.subheader("📈 5-Year Investment Projection")
    
    years = list(range(1, 6))
    property_value = [purchase_price * ((1 + appreciation_rate/100) ** y) for y in years]
    rental_income = [current_rent * 12 * ((1 + 0.03) ** y) * (1 - vacancy_rate/100) for y in years]
    total_returns = [property_value[y] + rental_income[y] for y in range(5)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=property_value, name='Property Value', mode='lines+markers', line=dict(color='#4f8df5', width=3)))
    fig.add_trace(go.Scatter(x=years, y=rental_income, name='Cumulative Rent', mode='lines+markers', line=dict(color='#10b981', width=3)))
    fig.add_trace(go.Scatter(x=years, y=total_returns, name='Total Returns', mode='lines+markers', line=dict(color='#a78bfa', width=3)))
    fig.update_layout(title="5-Year Wealth Creation Projection", xaxis_title="Years", yaxis_title="Amount (₹)", template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 4: DEAL FINDER ====================
with tabs[4]:
    st.subheader("🎯 AI Deal Finder")
    st.markdown("Discover undervalued properties with detailed analysis")
    
    np.random.seed(42)
    n_listings = 15
    
    listings = pd.DataFrame({
        'ID': [f"P{100+i}" for i in range(n_listings)],
        'City': [np.random.choice(df['city'].unique()) for _ in range(n_listings)],
        'Area': [np.random.randint(700, 2000) for _ in range(n_listings)],
        'Beds': [np.random.randint(1, 4) for _ in range(n_listings)],
        'Baths': [np.random.randint(1, 3) for _ in range(n_listings)],
        'Listed Price': [np.random.randint(20000, 75000) for _ in range(n_listings)]
    })
    
    fair_prices = []
    for _, row in listings.iterrows():
        input_row = create_input_row(row['Area'], row['Beds'], row['Baths'], 1, row['City'], 'Semi-Furnished', 
                                     df['area_rate'].mean(), df, features)
        fair = model.predict(input_row)[0] if input_row is not None else row['Listed Price']
        fair_prices.append(fair)
    
    listings['Fair Price'] = fair_prices
    listings['Discount'] = ((listings['Fair Price'] - listings['Listed Price']) / listings['Fair Price'] * 100)
    listings['Savings'] = (listings['Fair Price'] - listings['Listed Price']).clip(lower=0)
    listings['Deal Score'] = listings['Discount'].clip(0, 100).round(1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_city = st.multiselect("🏙️ Filter by City", df['city'].unique(), default=[city])
    with col2:
        min_discount = st.slider("💰 Minimum Discount %", 0, 50, 10, key="deal_min_discount")
    with col3:
        max_price = st.number_input("💵 Max Price (₹)", value=int(df['rent'].max()), key="deal_max_price")
    
    filtered = listings[
        (listings['City'].isin(filter_city)) &
        (listings['Discount'] >= min_discount) &
        (listings['Listed Price'] <= max_price)
    ].sort_values('Deal Score', ascending=False)
    
    if len(filtered) > 0:
        st.success(f"🎉 Found {len(filtered)} potential deals!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Avg Discount", f"{filtered['Discount'].mean():.1f}%")
        with col2:
            st.metric("💰 Max Savings", f"₹{filtered['Savings'].max():,.0f}")
        with col3:
            st.metric("💵 Total Savings", f"₹{filtered['Savings'].sum():,.0f}")
        
        st.markdown("---")
        
        for _, deal in filtered.head(5).iterrows():
            deal_color = '#10b981' if deal['Discount'] > 20 else '#f59e0b' if deal['Discount'] > 10 else '#3b82f6'
            deal_badge = '🔥 HOT DEAL' if deal['Discount'] > 20 else '👍 GOOD DEAL' if deal['Discount'] > 10 else '📊 FAIR DEAL'
            
            st.markdown(f"""
            <div class="deal-card" style="border-left-color: {deal_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #f1f5f9;">{deal['City']}</span>
                        <span style="color: #94a3b8;"> | {deal['Area']} sqft | {deal['Beds']} BHK | {deal['Baths']} Bath</span>
                    </div>
                    <div>
                        <span style="background: {deal_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; color: white;">
                            {deal_badge}
                        </span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px; flex-wrap: wrap; gap: 10px;">
                    <div><span style="color: #94a3b8;">Listed:</span> <span style="color: #f1f5f9;">₹{deal['Listed Price']:,.0f}</span></div>
                    <div><span style="color: #94a3b8;">Fair:</span> <span style="color: #4f8df5;">₹{deal['Fair Price']:,.0f}</span></div>
                    <div><span style="color: #94a3b8;">Save:</span> <span style="color: #10b981;">₹{deal['Savings']:,.0f}</span></div>
                    <div><span style="color: #94a3b8;">Discount:</span> <span style="color: #f59e0b;">{deal['Discount']:.1f}%</span></div>
                </div>
                <div style="margin-top: 12px;">
                    <div style="background: #334155; border-radius: 10px; height: 8px; overflow: hidden;">
                        <div style="width: {min(deal['Deal Score'], 100)}%; background: linear-gradient(90deg, {deal_color}, #10b981); height: 100%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"⭐ Save to Favorites", key=f"save_deal_{deal['ID']}"):
                st.session_state.favorites.append({
                    'id': deal['ID'],
                    'city': deal['City'],
                    'area': deal['Area'],
                    'beds': deal['Beds'],
                    'price': deal['Listed Price'],
                    'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.toast(f"✅ Property {deal['ID']} saved to favorites!", icon="⭐")
    else:
        st.info("No deals found with current filters. Try adjusting your criteria.")
    
    with st.expander("💡 Deal Finding Tips"):
        st.markdown("""
        - **Discount > 20%** : Excellent deal - act fast!
        - **Discount 10-20%** : Good deal - worth considering
        - **Discount < 10%** : Fair deal - check location and condition
        - Always verify property condition before making an offer
        - Use the Negotiation Assistant to get the best price
        """)

# ==================== TAB 5: NEGOTIATION ====================
with tabs[5]:
    st.subheader("🤝 AI Negotiation Assistant")
    st.markdown("Get AI-powered negotiation strategies based on market conditions")
    
    current_rent = st.session_state.base_pred or df['rent'].median()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Negotiation Parameters")
        asking_price = st.number_input("💰 Landlord's Asking Price", 
                                       value=int(current_rent * 1.15),
                                       step=5000,
                                       key="nego_asking")
        urgency = st.select_slider("⏰ Your Urgency", 
                                   options=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
                                   value='Medium',
                                   key="nego_urgency")
        market_days = st.slider("📅 Days on Market", 0, 180, 30,
                                help="Longer time indicates more negotiation power",
                                key="nego_market_days")
        property_condition = st.select_slider("🏠 Property Condition", 
                                              options=['Poor', 'Fair', 'Good', 'Excellent', 'Renovated'],
                                              value='Good',
                                              key="nego_condition")
    
    with col2:
        fair_price = current_rent
        diff_pct = ((asking_price - fair_price) / fair_price) * 100
        diff_pct = max(-100, min(100, diff_pct))
        
        st.metric("🏠 Fair Market Price", f"₹{fair_price:,.0f}")
        st.metric("📊 Difference", f"{diff_pct:.1f}%", 
                 delta="Above Market" if diff_pct > 0 else "Below Market",
                 delta_color="inverse" if diff_pct > 0 else "normal")
        
        # Landlord Motivation Meter
        motivation_score = 0
        if market_days > 60:
            motivation_score += 40
        elif market_days > 30:
            motivation_score += 20
        if diff_pct > 15:
            motivation_score += 30
        elif diff_pct > 5:
            motivation_score += 15
        
        st.progress(min(motivation_score, 100)/100, text=f"🤝 Landlord Motivation: {motivation_score}%")
        
        base_offer = fair_price
        if urgency in ['High', 'Very High']:
            offer_multiplier = 0.95
            strategy = "Aggressive (5% below market) - Move fast"
        elif urgency == 'Medium':
            offer_multiplier = 0.92
            strategy = "Balanced (8% below market) - Good starting point"
        else:
            offer_multiplier = 0.88
            strategy = "Conservative (12% below market) - Take your time"
        
        if market_days > 60:
            offer_multiplier -= 0.03
        if property_condition in ['Poor', 'Fair']:
            offer_multiplier -= 0.05
        elif property_condition == 'Excellent':
            offer_multiplier += 0.02
        
        opening_offer = base_offer * offer_multiplier
        expected_savings = asking_price - opening_offer
        
        st.success(f"💡 **Suggested Opening Offer:** ₹{opening_offer:,.0f}")
        st.info(f"📋 **Strategy:** {strategy}")
        st.metric("💰 Expected Savings", f"₹{expected_savings:,.0f}")
    
    st.markdown("---")
    st.markdown("### 💬 Key Talking Points")
    
    points = [
        f"• Market analysis shows fair rent is ₹{fair_price:,.0f}",
        f"• Asking price is {diff_pct:.1f}% above market rate",
        f"• Property has been on market for {market_days} days"
    ]
    
    if market_days > 60:
        points.append("• Long market presence indicates price is too high - use this leverage")
    if diff_pct > 20:
        points.append("• Property is significantly overpriced - strong negotiation position")
    if property_condition in ['Poor', 'Fair']:
        points.append("• Condition justifies lower price - request repairs or discount")
    if urgency in ['High', 'Very High']:
        points.append("• Show readiness to close quickly as leverage")
    
    for point in points:
        st.markdown(f"• {point}")
    
    st.markdown("---")
    st.markdown("### 📧 Email Script Generator")
    
    if st.button("📧 Generate Professional Email Script", key="gen_email_btn", use_container_width=True):
        email_script = f"""
Subject: Offer for Property - Market Analysis Based

Dear [Landlord/Agent Name],

I am writing to express my interest in the property located in {city}.

After conducting thorough market research and using AI-powered real estate analytics, 
I would like to submit an offer of ₹{opening_offer:,.0f} per month.

Key points from my analysis:
- Fair market rent for similar properties: ₹{fair_price:,.0f}
- Current asking price is {diff_pct:.1f}% above market
- Property has been on market for {market_days} days

I believe this offer reflects the true market value of the property. 
I am ready to move forward quickly upon agreement.

Looking forward to your positive response.

Best regards,
{full_name}
"""
        st.code(email_script, language="markdown")
        st.info("💡 Copy this email and customize it before sending!")
    
    with st.expander("💡 Pro Negotiation Tips"):
        st.markdown("""
        ### 🎯 Before You Negotiate:
        - **Research thoroughly** - Know the market rates in the area
        - **Get pre-approved** - Shows you're a serious buyer
        - **Be flexible** - Consider concessions like repairs or furnishings
        
        ### 💬 During Negotiation:
        - **Start lower** than your target - gives room to negotiate up
        - **Highlight market data** - use our analysis to justify your offer
        - **Be ready to walk away** - shows you're not desperate
        - **Ask for concessions** - if price is firm, negotiate for repairs or furnishings
        
        ### 📅 Timing Matters:
        - **Month-end** - Agents may be desperate to meet quotas
        - **Quarter-end** - Even better for negotiations
        - **Winter months** - Typically slower market, better deals
        """)

# ==================== TAB 6: FAVORITES ====================
with tabs[6]:
    st.subheader("⭐ My Saved Properties")
    st.markdown("Properties you've saved for future reference")
    
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.markdown(f"""
            <div class="favorite-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: bold; color: #f59e0b;">{fav['city']}</span>
                        <span style="color: #94a3b8;"> | {fav['area']} sqft | {fav['beds']} BHK</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.7rem;">Saved: {fav['saved_at']}</div>
                </div>
                <div style="margin-top: 8px;">
                    <span style="color: #94a3b8;">Estimated Price:</span>
                    <span style="color: #4f8df5; font-weight: bold;">₹{fav['price']:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Favorites", key="clear_fav_btn"):
            st.session_state.favorites = []
            st.rerun()
    else:
        st.markdown("""
        <div style="background: #0f172a; border-radius: 12px; padding: 40px; text-align: center;">
            <div style="font-size: 3rem;">⭐</div>
            <div style="color: #94a3b8;">No saved properties yet</div>
            <div style="color: #64748b;">Click "⭐ Save" on deals you like!</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== TAB 7: PROFILE ====================
with tabs[7]:
    st.markdown("### 👤 My Profile")
    
    created_date = user.get('created_at', 'N/A')
    if created_date != 'N/A' and len(str(created_date)) > 10:
        created_date = str(created_date)[:10]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e, #0f1923); border-radius: 20px; padding: 25px; margin-bottom: 20px; border: 1px solid rgba(79, 141, 245, 0.3);">
        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #4f8df5, #6c5ce7); 
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 2.5rem;">👤</span>
            </div>
            <div style="flex: 1;">
                <h2 style="margin: 0; color: #f1f5f9;">{full_name}</h2>
                <p style="margin: 5px 0; color: #94a3b8;">{user.get('email', '')}</p>
                <p style="margin: 5px 0; color: #64748b; font-size: 0.85rem;">Member since: {created_date}</p>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(79, 141, 245, 0.2); padding: 8px 16px; border-radius: 40px;">
                    <span style="color: #4f8df5;">✓ Verified Account</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pred_count = len(st.session_state.prediction_history)
    alert_count = len(st.session_state.alerts)
    fav_count = len(st.session_state.favorites)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem;">📊</div>
            <div style="font-size: 2rem; font-weight: bold; color: #4f8df5;">{pred_count}</div>
            <div style="color: #94a3b8;">Total Predictions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if pred_count > 0:
            avg_pred = np.mean([p['rent'] for p in st.session_state.prediction_history])
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2rem;">💰</div>
                <div style="font-size: 1.6rem; font-weight: bold; color: #a78bfa;">₹{avg_pred:,.0f}</div>
                <div style="color: #94a3b8;">Average Prediction</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2rem;">🔍</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #94a3b8;">No data</div>
                <div style="color: #64748b;">Make a prediction</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem;">🔔</div>
            <div style="font-size: 2rem; font-weight: bold; color: #f59e0b;">{alert_count}</div>
            <div style="color: #94a3b8;">Active Alerts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 2rem;">⭐</div>
            <div style="font-size: 2rem; font-weight: bold; color: #10b981;">{fav_count}</div>
            <div style="color: #94a3b8;">Saved Properties</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📋 Recent Predictions")
    
    if st.session_state.prediction_history:
        for pred in st.session_state.prediction_history[-5:][::-1]:
            st.markdown(f"""
            <div class="prediction-item">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="color: #4f8df5; font-weight: bold; font-size: 1.1rem;">₹{pred['rent']:,.0f}</span>
                        <span style="color: #94a3b8;"> / month</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.8rem;">{pred['timestamp']}</div>
                </div>
                <div style="margin-top: 8px; color: #94a3b8;">
                    📍 {pred['city']} | 📐 {pred['area']} sqft | 🛏️ {pred.get('beds', 'N/A')} BHK
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear History", key="clear_history_btn", use_container_width=True):
            st.session_state.prediction_history = []
            st.rerun()
    else:
        st.markdown("""
        <div style="background: #0f172a; border-radius: 12px; padding: 40px; text-align: center;">
            <div style="font-size: 3rem;">📭</div>
            <div style="color: #94a3b8;">No predictions yet</div>
            <div style="color: #64748b;">Use the sidebar to predict rent</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🔔 Active Price Alerts")
    
    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            st.markdown(f"""
            <div class="alert-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #f59e0b; font-weight: bold;">₹{alert['target']:,.0f}</span>
                        <span style="color: #94a3b8;"> in {alert['city']}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.7rem;">{alert['created']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Alerts", key="clear_alerts_btn", use_container_width=True):
            st.session_state.alerts = []
            st.rerun()
    else:
        st.markdown("""
        <div style="background: #0f172a; border-radius: 12px; padding: 40px; text-align: center;">
            <div style="font-size: 3rem;">🔕</div>
            <div style="color: #94a3b8;">No active alerts</div>
            <div style="color: #64748b;">Set price alerts in the sidebar</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📄 Generate Comprehensive Report")
    st.markdown("Get a complete PDF report including Valuation & Investment analysis")
    
    if st.button("📑 Generate Comprehensive Report", key="gen_report_btn", use_container_width=True):
        if st.session_state.base_pred and st.session_state.current_property:
            with st.spinner("Generating comprehensive report..."):
                prop = st.session_state.current_property
                rent = st.session_state.base_pred
                price = int(rent * 200)
                
                emi = price * 0.8 * 0.008
                monthly_cash_flow = rent - emi
                roi = ((rent * 12) / (price * 0.2)) * 100
                cap_rate = ((rent * 12) / price) * 100
                
                financials = {
                    'purchase_price': price,
                    'down_payment': price * 0.2,
                    'down_payment_pct': 20,
                    'loan_amount': price * 0.8,
                    'interest_rate': 8.5,
                    'loan_years': 20,
                    'annual_yield': (rent * 12 / price) * 100,
                    'emi': emi,
                    'roi': roi,
                    'cap_rate': cap_rate,
                    'monthly_cash_flow': monthly_cash_flow
                }
                
                pdf_bytes = create_comprehensive_report(
                    city=prop['city'],
                    rent=rent,
                    area=prop['area'],
                    beds=prop['beds'],
                    baths=prop['baths'],
                    balconies=prop['balconies'],
                    furn=prop['furnishing'],
                    username=user['username'],
                    full_name=full_name,
                    features_importance=importance_df if importance_df is not None else pd.DataFrame(),
                    financials=financials
                )
                
                if pdf_bytes:
                    st.download_button(
                        label="📥 Download Comprehensive Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"property_report_{user['username']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_report_btn"
                    )
                    st.success("✅ Report generated! Click download button above.")
                else:
                    st.error("❌ Failed to generate report")
        else:
            st.warning("⚠️ Make a prediction first to generate a report")
    
    st.markdown("---")
    
    with st.expander("📥 Export All My Data (CSV)"):
        if st.session_state.prediction_history:
            history_df = pd.DataFrame(st.session_state.prediction_history)
            csv = history_df.to_csv(index=False)
            st.download_button(
                label="Download Predictions CSV",
                data=csv,
                file_name=f"predictions_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_csv_btn"
            )
        else:
            st.info("No prediction data to export")

# ==================== FOOTER ====================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📊 Properties: {len(df)}")
with col2:
    st.caption(f"🏙️ Cities: {len(df['city'].unique())}")
with col3:
    if st.session_state.last_prediction:
        st.caption(f"💰 Last Prediction: ₹{st.session_state.last_prediction:,.0f}")
        

# Add floating chatbot - Native Streamlit component
from utils.chatbot import inject_chat_widget
inject_chat_widget(df)

