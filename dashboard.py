# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import datetime
import hashlib
import json
import os
from PIL import Image
import time

# Page config must be first
st.set_page_config(
    page_title="RealEstate AI Pro",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
    }
    .css-1aumxhk {
        background-color: #f0f2f6;
    }
    .highlight {
        background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==================== USER AUTHENTICATION ====================
def hash_password(password):
    return hashlib.sha256256(password.encode()).hexdigest()

def init_users_db():
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as f:
            json.dump({}, f)

def save_user(username, password):
    with open('users.json', 'r') as f:
        users = json.load(f)
    users[username] = hash_password(password)
    with open('users.json', 'w') as f:
        json.dump(users, f)

def check_user(username, password):
    with open('users.json', 'r') as f:
        users = json.load(f)
    return username in users and users[username] == hash_password(password)

init_users_db()

# ==================== DATA LOADING & ENGINEERING ====================
@st.cache_data
def load_and_engineer_data():
    df = pd.read_csv('data.csv')
    
    # Basic features
    df['price_per_sqft'] = df['rent'] / df['area']
    furnish_map = {'Furnished': 2, 'Semi-Furnished': 1, 'Unfurnished': 0}
    df['furnish_score'] = df['furnishing'].map(furnish_map)
    df['luxury_score'] = df['bathrooms'] + df['balconies'] + df['furnish_score']
    
    # Market dynamics
    city_avg = df.groupby('city')['area_rate'].transform('mean')
    df['is_premium_area'] = (df['area_rate'] > city_avg).astype(int)
    
    # Simulate time data (if not present in original)
    np.random.seed(42)
    df['month'] = np.random.randint(1, 13, len(df))
    df['year'] = 2025
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
    
    # Season
    season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                  3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer',
                  9: 'Fall', 10: 'Fall', 11: 'Fall'}
    df['season'] = df['month'].map(season_map)
    
    # Market velocity (simulated)
    df['market_velocity'] = df.groupby('city')['rent'].transform(
        lambda x: x.pct_change().fillna(np.random.uniform(-0.1, 0.1, len(x)))
    )
    
    return df

df = load_and_engineer_data()

# ==================== AI MODEL TRAINING ====================
@st.cache_resource
def train_model(data):
    # Prepare features
    df_ml = pd.get_dummies(data, columns=['city', 'furnishing'], drop_first=True)
    feature_cols = [col for col in df_ml.columns if col not in ['rent', 'house_type', 'locality', 'price_per_sqft', 'date', 'year', 'month', 'season']]
    X = df_ml[feature_cols]
    y = df_ml['rent']
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    # Calculate feature importance
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    return model, X.columns.tolist(), importance_df

model, model_columns, feature_importance = train_model(df)

# ==================== HELPER FUNCTIONS ====================
def create_input_row(area, beds, baths, balc, city, furn, rate):
    """Create model input row from user selections"""
    row = pd.DataFrame([[area, beds, baths, balc, rate]], 
                       columns=['area', 'beds', 'bathrooms', 'balconies', 'area_rate'])
    
    # Add luxury score
    f_val = 2 if furn == 'Furnished' else 1 if furn == 'Semi-Furnished' else 0
    row['luxury_score'] = baths + balc + f_val
    
    # Add premium area flag
    city_avg_val = df[df['city'] == city]['area_rate'].mean()
    row['is_premium_area'] = 1 if rate > city_avg_val else 0
    
    # Add one-hot encoded columns
    for col in model_columns:
        if col not in row.columns:
            if col.startswith('city_'):
                row[col] = 1 if f"city_{city}" == col else 0
            elif col.startswith('furnishing_'):
                row[col] = 1 if f"furnishing_{furn}" == col else 0
            else:
                row[col] = 0
    
    return row[model_columns]

def check_alerts():
    """Check if any price alerts are triggered"""
    if 'alerts' in st.session_state and 'base_pred' in st.session_state:
        for i, alert in enumerate(st.session_state['alerts']):
            if abs(st.session_state['base_pred'] - alert['target']) / alert['target'] < 0.1:
                st.toast(f"🎯 Alert {i+1}: Price now within 10% of ₹{alert['target']:,.0f}!")
                # Remove triggered alert
                st.session_state['alerts'].pop(i)
                break

def get_market_sentiment(city):
    """Get market sentiment for a city"""
    city_data = df[df['city'] == city]
    avg_rent = city_data['rent'].mean()
    avg_velocity = city_data['market_velocity'].mean()
    
    if avg_velocity > 0.05:
        return "🔥 Hot Market", "Rising fast"
    elif avg_velocity > 0:
        return "📈 Warming Up", "Moderate growth"
    elif avg_velocity > -0.05:
        return "📊 Stable", "No significant change"
    else:
        return "❄️ Cooling Down", "Prices decreasing"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/real-estate.png", width=80)
    st.title("🏙️ RealEstate AI Pro")
    st.markdown("---")
    
    # User Authentication
    if 'user' not in st.session_state:
        with st.expander("🔐 Login / Sign Up", expanded=True):
            auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
            
            with auth_tab1:
                login_user = st.text_input("Username", key="login_user")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                if st.button("Login", key="login_btn"):
                    if check_user(login_user, login_pass):
                        st.session_state['user'] = login_user
                        st.session_state['user_since'] = datetime.datetime.now().strftime("%Y-%m-%d")
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            
            with auth_tab2:
                new_user = st.text_input("Choose Username", key="new_user")
                new_pass = st.text_input("Choose Password", type="password", key="new_pass")
                confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass")
                if st.button("Sign Up", key="signup_btn"):
                    if new_pass == confirm_pass:
                        save_user(new_user, new_pass)
                        st.success("Account created! Please login.")
                    else:
                        st.error("Passwords don't match")
    
    else:
        st.success(f"👋 Welcome, {st.session_state['user']}!")
        st.caption(f"Member since {st.session_state.get('user_since', 'Today')}")
        if st.button("🚪 Logout"):
            del st.session_state['user']
            st.rerun()
    
    st.markdown("---")
    
    # Property Details Input
    st.header("🏠 Property Details")
    
    col1, col2 = st.columns(2)
    with col1:
        s_city = st.selectbox("City", df['city'].unique())
        s_area = st.number_input("Area (sqft)", 100, 10000, 1200)
        s_beds = st.slider("Bedrooms", 1, 10, 2)
    with col2:
        s_furn = st.selectbox("Furnishing", df['furnishing'].unique())
        s_baths = st.slider("Bathrooms", 1, 10, 2)
        s_balc = st.slider("Balconies", 0, 10, 1)
    
    s_rate = st.number_input("Locality Rate (₹/sqft)", 
                             value=float(df['area_rate'].median()),
                             help="Average price per sqft in this locality")
    
    # Price Alert System
    with st.expander("🔔 Set Price Alert"):
        alert_price = st.number_input("Alert me when rent crosses (₹)", 
                                     value=int(df['rent'].median()))
        if st.button("Set Alert"):
            if 'alerts' not in st.session_state:
                st.session_state['alerts'] = []
            st.session_state['alerts'].append({
                'target': alert_price,
                'city': s_city,
                'created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("✅ Alert set! You'll be notified when prices approach this target.")
    
    # Predict Button
    st.markdown("---")
    if st.button("🚀 Predict Fair Rent", use_container_width=True):
        with st.spinner("AI analyzing market data..."):
            time.sleep(1)  # Simulate processing
            input_row = create_input_row(s_area, s_beds, s_baths, s_balc, s_city, s_furn, s_rate)
            prediction = model.predict(input_row)[0]
            st.session_state['base_pred'] = prediction
            
            # Store last prediction details
            st.session_state['last_prediction'] = {
                'city': s_city,
                'rent': prediction,
                'area': s_area,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
    
    # Initialize session state with default prediction if not exists
    if 'base_pred' not in st.session_state:
        st.session_state['base_pred'] = float(df['rent'].median())
    
    # Show current prediction
    st.metric(
        label="💰 Current Fair Rent Estimate",
        value=f"₹{st.session_state['base_pred']:,.0f}",
        delta=f"Based on {s_city} market"
    )
    
    # Check alerts after prediction
    check_alerts()

# ==================== MAIN CONTENT ====================
# Welcome banner for new users
if 'user' not in st.session_state:
    st.markdown("""
    <div class="highlight">
        <h2>🏙️ Welcome to RealEstate AI Pro</h2>
        <p>Your intelligent partner for real estate decisions. Login to unlock personalized features!</p>
    </div>
    """, unsafe_allow_html=True)

# Create tabs
tabs = st.tabs([
    "📊 Market Intelligence",
    "⚖️ Smart Comparison",
    "🧠 AI What-If Analyzer",
    "💰 Investment Calculator",
    "🎯 Deal Finder",
    "🤝 Negotiation Assistant"
])

# ==================== TAB 1: MARKET INTELLIGENCE ====================
with tabs[0]:
    st.subheader("📊 Market Intelligence Dashboard")
    
    # Market sentiment cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        sentiment, trend = get_market_sentiment(s_city)
        st.metric("Market Sentiment", sentiment, trend)
    
    with col_m2:
        city_avg = df[df['city'] == s_city]['rent'].mean()
        st.metric(f"Avg Rent in {s_city}", f"₹{city_avg:,.0f}")
    
    with col_m3:
        premium_pct = (df[df['city'] == s_city]['is_premium_area'].mean() * 100)
        st.metric("Premium Areas %", f"{premium_pct:.1f}%")
    
    with col_m4:
        inventory = len(df[df['city'] == s_city])
        st.metric("Available Listings", inventory)
    
    st.markdown("---")
    
    # Charts
    col_ch1, col_ch2 = st.columns(2)
    
    with col_ch1:
        # Rent distribution by city
        fig1 = px.box(df, x='city', y='rent', color='city',
                     title="🏘️ Rent Distribution by City",
                     labels={'rent': 'Monthly Rent (₹)', 'city': 'City'})
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_ch2:
        # Size vs Price with luxury score
        fig2 = px.scatter(df, x='area', y='rent', color='luxury_score',
                         size='bathrooms', hover_data=['city', 'furnishing'],
                         title="📏 Size vs Price Analysis",
                         labels={'area': 'Area (sqft)', 'rent': 'Monthly Rent (₹)'})
        st.plotly_chart(fig2, use_container_width=True)
    
    # Feature importance
    st.subheader("🔑 Key Factors Influencing Rent")
    fig3 = px.bar(feature_importance.head(10), x='importance', y='feature',
                  orientation='h', title="Top 10 Features Affecting Rent",
                  labels={'importance': 'Importance Score', 'feature': ''})
    st.plotly_chart(fig3, use_container_width=True)
    
    # Seasonal trends
    seasonal = df.groupby(['city', 'season'])['rent'].mean().reset_index()
    fig4 = px.line(seasonal[seasonal['city'] == s_city], x='season', y='rent',
                   title=f"📅 Seasonal Trends in {s_city}",
                   labels={'season': 'Season', 'rent': 'Average Rent (₹)'})
    st.plotly_chart(fig4, use_container_width=True)

# ==================== TAB 2: SMART COMPARISON ====================
with tabs[1]:
    st.subheader("⚖️ Smart Property Comparison")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### Property A")
        city_a = st.selectbox("City A", df['city'].unique(), key='city_a')
        area_a = st.number_input("Area A (sqft)", 100, 10000, 1000, key='area_a')
        beds_a = st.slider("Bedrooms A", 1, 10, 2, key='beds_a')
        furn_a = st.selectbox("Furnishing A", df['furnishing'].unique(), key='furn_a')
        
        # Predict for Property A
        input_a = create_input_row(area_a, beds_a, 2, 1, city_a, furn_a, 
                                  df[df['city'] == city_a]['area_rate'].mean())
        rent_a = model.predict(input_a)[0]
        
    with col_c2:
        st.markdown("### Property B")
        city_b = st.selectbox("City B", df['city'].unique(), key='city_b')
        area_b = st.number_input("Area B (sqft)", 100, 10000, 1200, key='area_b')
        beds_b = st.slider("Bedrooms B", 1, 10, 3, key='beds_b')
        furn_b = st.selectbox("Furnishing B", df['furndf['furnishing'].unique(), key='furn_b')
        
        # Predict for Property B
        input_b = create_input_row(area_b, beds_b, 2, 1, city_b, furn_b,
                                  df[df['city'] == city_b]['area_rate'].mean())
        rent_b = model.predict(input_b)[0]
    
    # Comparison metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.metric("Property A Rent", f"₹{rent_a:,.0f}")
        st.caption(f"{area_a} sqft in {city_a}")
    
    with col_m2:
        diff = rent_b - rent_a
        st.metric("Property B Rent", f"₹{rent_b:,.0f}", 
                 delta=f"₹{diff:,.0f}" if diff != 0 else None)
        st.caption(f"{area_b} sqft in {city_b}")
    
    with col_m3:
        value_score_a = rent_a / area_a
        value_score_b = rent_b / area_b
        better_value = "A" if value_score_a < value_score_b else "B"
        st.metric("Best Value", f"Property {better_value}")
        st.caption("Lower ₹/sqft = Better value")
    
    # Visual comparison
    comp_df = pd.DataFrame({
        'Property': ['A', 'B'],
        'City': [city_a, city_b],
        'Area': [area_a, area_b],
        'Estimated Rent': [rent_a, rent_b]
    })
    
    fig_comp = px.bar(comp_df, x='Property', y='Estimated Rent', color='City',
                      title="Property Comparison",
                      text_auto='.2s',
                      labels={'Estimated Rent': 'Monthly Rent (₹)'})
    st.plotly_chart(fig_comp, use_container_width=True)

# ==================== TAB 3: AI WHAT-IF ANALYZER ====================
with tabs[2]:
    st.subheader("🧠 AI What-If Simulator")
    st.markdown("See how changes to your property affect rent")
    
    col_in, col_out = st.columns([1, 1])
    
    with col_in:
        st.markdown("### Modify Your Property")
        
        modifications = st.multiselect(
            "Select modifications to simulate",
            ["Add Bedroom", "Add Bathroom", "Add Balcony", 
             "Upgrade Furnishing", "Increase Area", "Premium Locality"]
        )
        
        # Apply modifications
        sim_area = s_area
        sim_beds = s_beds
        sim_baths = s_baths
        sim_balc = s_balc
        sim_furn = s_furn
        sim_rate = s_rate
        
        cost_estimate = 0
        
        for mod in modifications:
            if mod == "Add Bedroom":
                sim_beds += 1
                cost_estimate += 500000
            elif mod == "Add Bathroom":
                sim_baths += 1
                cost_estimate += 300000
            elif mod == "Add Balcony":
                sim_balc += 1
                cost_estimate += 150000
            elif mod == "Upgrade Furnishing":
                if sim_furn == "Unfurnished":
                    sim_furn = "Semi-Furnished"
                    cost_estimate += 200000
                elif sim_furn == "Semi-Furnished":
                    sim_furn = "Furnished"
                    cost_estimate += 300000
            elif mod == "Increase Area":
                sim_area = int(s_area * 1.2)
                cost_estimate += 2000000
            elif mod == "Premium Locality":
                sim_rate = s_rate * 1.3
                cost_estimate += 0  # Location premium is market-driven
        
        # Get simulation prediction
        sim_input = create_input_row(sim_area, sim_beds, sim_baths, sim_balc, 
                                    s_city, sim_furn, sim_rate)
        sim_rent = model.predict(sim_input)[0]
        rent_diff = sim_rent - st.session_state['base_pred']
        
        # ROI calculation
        monthly_increase = rent_diff
        annual_increase = monthly_increase * 12
        if cost_estimate > 0:
            roi_years = cost_estimate / annual_increase if annual_increase > 0 else float('inf')
        else:
            roi_years = 0
    
    with col_out:
        st.markdown("### Impact Analysis")
        
        # Metrics
        met1, met2, met3 = st.columns(3)
        with met1:
            st.metric("Current Rent", f"₹{st.session_state['base_pred']:,.0f}")
        with met2:
            st.metric("New Rent", f"₹{sim_rent:,.0f}", 
                     delta=f"₹{rent_diff:,.0f}")
        with met3:
            st.metric("Monthly Δ", f"{((sim_rent/st.session_state['base_pred'])-1)*100:.1f}%")
        
        # Investment analysis
        if cost_estimate > 0:
            st.markdown("---")
            st.markdown("### 💰 Renovation ROI")
            
            col_roi1, col_roi2 = st.columns(2)
            with col_roi1:
                st.metric("Estimated Cost", f"₹{cost_estimate:,.0f}")
                st.metric("Annual Rent Increase", f"₹{annual_increase:,.0f}")
            with col_roi2:
                if roi_years != float('inf'):
                    st.metric("Payback Period", f"{roi_years:.1f} years")
                    if roi_years < 3:
                        st.success("✅ Excellent ROI!")
                    elif roi_years < 5:
                        st.info("📊 Good ROI")
                    else:
                        st.warning("⚠️ Long payback period")
                else:
                    st.warning("No positive ROI from these changes")
        
        # Visual comparison
        comp_data = pd.DataFrame({
            'Scenario': ['Current', 'After Modifications'],
            'Rent': [st.session_state['base_pred'], sim_rent]
        })
        
        fig_sim = px.bar(comp_data, x='Scenario', y='Rent',
                        color='Scenario',
                        title="Rent Impact Visualization",
                        text_auto='.2s')
        st.plotly_chart(fig_sim, use_container_width=True)

# ==================== TAB 4: INVESTMENT CALCULATOR ====================
with tabs[3]:
    st.subheader("💰 Investment & ROI Calculator")
    
    col_inv1, col_inv2 = st.columns(2)
    
    with col_inv1:
        st.markdown("### Property Details")
        purchase_price = st.number_input("Purchase Price (₹)", 
                                        value=int(st.session_state['base_pred'] * 200), 
                                        step=100000)
        down_payment_pct = st.slider("Down Payment %", 10, 50, 20)
        loan_years = st.slider("Loan Tenure (Years)", 5, 30, 20)
        interest_rate = st.slider("Interest Rate %", 6.0, 12.0, 8.5)
        
        # Additional costs
        registration = purchase_price * 0.05
        maintenance = st.number_input("Monthly Maintenance (₹)", 1000, 10000, 3000)
        property_tax = purchase_price * 0.002  # 0.2% annual
        
    with col_inv2:
        st.markdown("### Returns Analysis")
        
        # Loan calculation
        loan_amount = purchase_price * (1 - down_payment_pct/100)
        monthly_rate = interest_rate / 12 / 100
        months = loan_years * 12
        
        if monthly_rate > 0:
            emi = loan_amount * monthly_rate * (1 + monthly_rate)**months / ((1 + monthly_rate)**months - 1)
        else:
            emi = loan_amount / months
        
        # Income & expenses
        monthly_rental = st.session_state['base_pred']
        annual_rental = monthly_rental * 12
        annual_expenses = (maintenance * 12) + property_tax
        annual_net_income = annual_rental - annual_expenses
        annual_loan_payment = emi * 12
        
        # Cash flow
        cash_flow = annual_net_income - annual_loan_payment
        
        # Metrics
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Down Payment", f"₹{purchase_price * down_payment_pct/100:,.0f}")
            st.metric("Monthly EMI", f"₹{emi:,.0f}")
            st.metric("Annual Net Income", f"₹{annual_net_income:,.0f}")
        with m2:
            roi = (annual_net_income / (purchase_price * down_payment_pct/100)) * 100
            st.metric("Cash-on-Cash ROI", f"{roi:.2f}%")
            st.metric("Monthly Cash Flow", f"₹{cash_flow/12:,.0f}")
            st.metric("Cap Rate", f"{(annual_net_income/purchase_price)*100:.2f}%")
        
        # Investment recommendation
        st.markdown("### 📊 Investment Recommendation")
        if cash_flow > 0 and roi > 12:
            st.success("✅ Excellent Investment! Positive cash flow with high ROI")
        elif cash_flow > 0 and roi > 8:
            st.info("📈 Good Investment - Positive cash flow")
        elif cash_flow > 0:
            st.warning("⚠️ Moderate Investment - Low but positive returns")
        else:
            st.error("❌ Poor Investment - Negative cash flow")

# ==================== TAB 5: DEAL FINDER ====================
with tabs[4]:
    st.subheader("🎯 AI Deal Finder")
    st.markdown("Find undervalued properties in your preferred area")
    
    # Generate sample listings (in production, this would be from API/database)
    np.random.seed(42)
    n_listings = 20
    
    sample_listings = pd.DataFrame({
        'id': range(1, n_listings + 1),
        'city': np.random.choice(df['city'].unique(), n_listings),
        'area': np.random.randint(800, 2500, n_listings),
        'beds': np.random.randint(1, 4, n_listings),
        'baths': np.random.randint(1, 3, n_listings),
        'furnishing': np.random.choice(['Furnished', 'Semi-Furnished', 'Unfurnished'], n_listings),
        'listed_price': np.random.randint(15000, 80000, n_listings)
    })
    
    # Calculate fair price for each listing
    fair_prices = []
    for _, row in sample_listings.iterrows():
        input_row = create_input_row(
            row['area'], row['beds'], row['baths'], 1, 
            row['city'], row['furnishing'],
            df[df['city'] == row['city']]['area_rate'].mean()
        )
        fair_prices.append(model.predict(input_row)[0])
    
    sample_listings['fair_price'] = fair_prices
    sample_listings['discount'] = ((sample_listings['fair_price'] - sample_listings['listed_price']) / 
                                   sample_listings['fair_price'] * 100)
    sample_listings['deal_score'] = sample_listings['discount'].clip(0, 100)
    
    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_city = st.multiselect("Filter by City", df['city'].unique(), default=[s_city])
    with col_f2:
        min_discount = st.slider("Minimum Discount %", 0, 50, 10)
    with col_f3:
        max_price = st.number_input("Max Price (₹)", value=int(df['rent'].max()))
    
    # Filter listings
    filtered = sample_listings[
        (sample_listings['city'].isin(filter_city)) &
        (sample_listings['discount'] >= min_discount) &
        (sample_listings['listed_price'] <= max_price)
    ].sort_values('deal_score', ascending=False)
    
    if len(filtered) > 0:
        st.success(f"Found {len(filtered)} potential deals!")
        
        # Display top deals
        for _, deal in filtered.head(5).iterrows():
            with st.container():
                col_d1, col_d2, col_d3, col_d4 = st.columns([2,1,1,1])
                with col_d1:
                    st.markdown(f"**{deal['city']}** - {deal['area']} sqft, {deal['beds']} BHK")
                with col_d2:
                    st.markdown(f"Listed: ₹{deal['listed_price']:,.0f}")
                with col_d3:
                    st.markdown(f"Fair: ₹{deal['fair_price']:,.0f}")
                with col_d4:
                    if deal['discount'] > 0:
                        st.markdown(f"💰 **{deal['discount']:.1f}% off**")
                    else:
                        st.markdown("⚠️ Overpriced")
                
                if deal['discount'] > 20:
                    st.progress(1.0, "🔥 Hot Deal!")
                elif deal['discount'] > 10:
                    st.progress(0.7, "👍 Good Deal")
                
                st.markdown("---")
    else:
        st.info("No deals found with current filters. Try adjusting your criteria.")

# ==================== TAB 6: NEGOTIATION ASSISTANT ====================
with tabs[5]:
    st.subheader("🤝 AI Negotiation Assistant")
    st.markdown("Get personalized negotiation strategies based on market conditions")
    
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        st.markdown("### Negotiation Parameters")
        landlord_price = st.number_input("Landlord's Asking Price (₹)", 
                                        value=int(st.session_state['base_pred'] * 1.15))
        urgency = st.select_slider("Your Urgency Level",
                                   options=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
                                   value='Medium')
        market_days = st.slider("Days on Market", 0, 180, 30)
        
    with col_n2:
        st.markdown("### Negotiation Strategy")
        
        fair_price = st.session_state['base_pred']
        overprice_pct = ((landlord_price - fair_price) / fair_price) * 100
        
        # Market leverage
        sentiment, _ = get_market_sentiment(s_city)
        if "🔥" in sentiment:
            market_leverage = "Landlord"
        elif "❄️" in sentiment:
            market_leverage = "Tenant"
        else:
            market_leverage = "Balanced"
        
        # Generate strategy
        st.metric("Market Leverage", market_leverage)
        st.metric("Overpriced by", f"{overprice_pct:.1f}%")
        
        # Opening offer
        if urgency in ['High', 'Very High']:
            opening_offer = fair_price * 0.95
            strategy = "Open with 5% below market rate (due to urgency)"
        else:
            opening_offer = fair_price * 0.85
            strategy = "Start with 15% below market rate"
        
        st.metric("Suggested Opening Offer", f"₹{opening_offer:,.0f}")
        
        # Talking points
        st.markdown("### 💬 Key Talking Points")
        points = [
            f"Market analysis shows fair rent is ₹{fair_price:,.0f}",
            f"Similar properties in {s_city} are priced {abs(overprice_pct):.1f}% {'above' if overprice_pct>0 else 'below'} this",
            f"Property has been on market for {market_days} days"
        ]
        
        if market_days > 60:
            points.append("Long market presence indicates price is too high")
        
        if overprice_pct > 20:
            points.append("This is significantly above market rate - we have strong negotiation power")
        
        for point in points:
            st.markdown(f"• {point}")
        
        # Download negotiation script
        if st.button("📝 Generate Negotiation Script"):
            script = f"""
            NEGOTIATION SCRIPT - {s_city}
            
            Opening: "Based on my AI analysis, the fair market rent for this property is ₹{fair_price:,.0f}. 
            Your asking price of ₹{landlord_price:,.0f} is {overprice_pct:.1f}% above market rate."
            
            Key Points:
            {chr(10).join(['- ' + p for p in points])}
            
            Closing: "I'd like to offer ₹{opening_offer:,.0f} which is a fair price based on market data."
            """
            st.download_button("Download Script", script, file_name="negotiation_script.txt")

# ==================== FOOTER ====================
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("🏙️ RealEstate AI Pro v2.0")
with col_f2:
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}")
with col_f3:
    if 'user' in st.session_state:
        st.caption(f"Logged in as: {st.session_state['user']}")