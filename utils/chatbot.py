# utils/chatbot.py
import streamlit as st
import pandas as pd
import difflib
from datetime import datetime
from collections import Counter

def fuzzy_match_city(user_input, cities_list):
    """Find closest matching city name even with typos"""
    user_input_lower = user_input.lower()
    
    # Handle special cases and common typos
    city_aliases = {
        'bangalore': 'Bangalore', 'bengaluru': 'Bangalore', 'banglore': 'Bangalore',
        'mumbai': 'Mumbai', 'bombay': 'Mumbai', 'mumbi': 'Mumbai',
        'delhi': 'Delhi', 'new delhi': 'Delhi', 'dilli': 'Delhi',
        'chennai': 'Chennai', 'madras': 'Chennai', 'chenai': 'Chennai',
        'pune': 'Pune', 'poona': 'Pune',
        'hyderabad': 'Hyderabad', 'secunderabad': 'Hyderabad',
        'nagpur': 'Nagpur', 'nagppur': 'Nagpur',
        'kolkata': 'Kolkata', 'calcutta': 'Kolkata'
    }
    
    for alias, correct in city_aliases.items():
        if alias in user_input_lower:
            if correct in cities_list:
                return correct
    
    # Direct match
    for city in cities_list:
        if city.lower() in user_input_lower:
            return city
    
    # Fuzzy matching for other typos
    matches = difflib.get_close_matches(user_input_lower, [c.lower() for c in cities_list], n=1, cutoff=0.6)
    if matches:
        for city in cities_list:
            if city.lower() == matches[0]:
                return city
    
    return None

def get_city_data(df, city):
    """Get comprehensive data for a specific city"""
    city_data = df[df['city'] == city]
    if city_data.empty:
        return None
    
    return {
        'avg_rent': city_data['rent'].mean(),
        'min_rent': city_data['rent'].min(),
        'max_rent': city_data['rent'].max(),
        'median_rent': city_data['rent'].median(),
        'count': len(city_data),
        'avg_area': city_data['area'].mean(),
        'avg_beds': city_data['beds'].mean()
    }

def get_city_market_outlook(df, city):
    """Get market outlook for a specific city"""
    city_data = get_city_data(df, city)
    if not city_data:
        return None
    
    # Get city ranking
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    rank = list(city_avg.index).index(city) + 1
    total_cities = len(city_avg)
    
    # Determine market position
    if rank <= total_cities // 3:
        position = "💰 Affordable Market"
        advice = "Great for budget-conscious renters and first-time investors"
    elif rank <= 2 * total_cities // 3:
        position = "📊 Mid-Range Market"
        advice = "Balanced market with good value for money"
    else:
        position = "💎 Premium Market"
        advice = "High-end market with luxury properties, best for long-term appreciation"
    
    return f"""📈 **{city} Market Outlook:**

🏷️ **Position:** {position} (Rank #{rank} of {total_cities})
💰 **Average Rent:** ₹{city_data['avg_rent']:,.0f}/month
📊 **Price Range:** ₹{city_data['min_rent']:,.0f} - ₹{city_data['max_rent']:,.0f}
📐 **Typical Area:** {city_data['avg_area']:.0f} sqft
🛏️ **Average Bedrooms:** {city_data['avg_beds']:.1f} BHK

💡 **Insight:** {advice}

{get_seasonal_insight()}"""

def get_overall_market_outlook(df):
    """Generate overall market outlook with hottest/cheapest cities"""
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    cheapest = city_avg.index[0]
    cheapest_price = city_avg.iloc[0]
    expensive = city_avg.index[-1]
    expensive_price = city_avg.iloc[-1]
    
    # Find city with best value (lowest price per sqft)
    df['price_per_sqft'] = df['rent'] / df['area']
    best_value_city = df.groupby('city')['price_per_sqft'].mean().idxmin()
    
    return f"""📈 **Overall Market Outlook:**

🔥 **Hottest Market:** {expensive} (₹{expensive_price:,.0f}/month)
💰 **Most Affordable:** {cheapest} (₹{cheapest_price:,.0f}/month)
⭐ **Best Value:** {best_value_city}

{get_seasonal_insight()}

💡 **Tip:** {cheapest} offers the best entry point for first-time investors. You can save {((expensive_price - cheapest_price)/expensive_price*100):.0f}% by choosing {cheapest} over {expensive}!"""

def get_city_investment_analysis(df, city):
    """Get investment analysis for a specific city"""
    city_data = get_city_data(df, city)
    if not city_data:
        return None
    
    avg_rent = city_data['avg_rent']
    estimated_price = avg_rent * 200
    gross_yield = (avg_rent * 12 / estimated_price) * 100
    
    # Calculate investment score
    if gross_yield > 7:
        score = "High"
        recommendation = "✅ GOOD INVESTMENT"
        risk = "Low"
    elif gross_yield > 5:
        score = "Medium"
        recommendation = "📊 MODERATE INVESTMENT"
        risk = "Medium"
    else:
        score = "Low"
        recommendation = "⚠️ CAUTION - Low Returns"
        risk = "High"
    
    # Get city ranking for context
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    rank = list(city_avg.index).index(city) + 1
    total_cities = len(city_avg)
    
    return f"""💰 **Investment Analysis for {city}:**

📊 **Key Metrics:**
• Average Rent: ₹{avg_rent:,.0f}/month
• Est. Property Price: ₹{estimated_price:,.0f}
• Gross Rental Yield: **{gross_yield:.1f}%**
• Market Position: #{rank} of {total_cities} cities

📈 **Investment Verdict:**
• Score: {score}
• Recommendation: {recommendation}
• Risk Level: {risk}

💡 Use the **'Investment'** tab for detailed EMI and cash flow analysis!"""

def get_city_comparison(df, city1, city2):
    """Get detailed comparison between two cities"""
    data1 = get_city_data(df, city1)
    data2 = get_city_data(df, city2)
    
    if not data1 or not data2:
        return None
    
    rent1 = data1['avg_rent']
    rent2 = data2['avg_rent']
    diff = abs(rent1 - rent2)
    cheaper = city1 if rent1 < rent2 else city2
    pct_diff = (diff / max(rent1, rent2)) * 100
    
    # Calculate yields
    yield1 = (rent1 * 12) / (rent1 * 200) * 100
    yield2 = (rent2 * 12) / (rent2 * 200) * 100
    
    return f"""⚖️ **{city1} vs {city2} Comparison:**

📊 **Rent Comparison:**
• {city1}: ₹{rent1:,.0f}/month
• {city2}: ₹{rent2:,.0f}/month
• {cheaper} is **{pct_diff:.0f}% cheaper** (₹{diff:,.0f}/month savings)

💰 **Investment Yield:**
• {city1}: {yield1:.1f}%
• {city2}: {yield2:.1f}%

💡 **Verdict:** {city1 if rent1 < rent2 else city2} is better for budget-conscious renters.
Use the **'Smart Compare'** tab for detailed property comparison!"""

def get_seasonal_insight():
    """Provide seasonal real estate insights"""
    month = datetime.now().month
    if month in [11, 12, 1, 2]:
        return "❄️ **Seasonal Insight:** Winter months (Nov-Feb) typically see lower demand. You may have better negotiation power (5-10% discounts possible)."
    elif month in [3, 4, 5]:
        return "🌸 **Seasonal Insight:** Spring months (Mar-May) see high demand. Prices tend to rise, so act fast on good deals!"
    else:
        return "☀️ **Seasonal Insight:** Summer/Fall (Jun-Oct) is a moderate market. Good time for long-term investments."

def get_user_personalization():
    """Get personalized insights based on user's prediction history"""
    pred_count = len(st.session_state.get('prediction_history', []))
    
    if pred_count > 10:
        return f"📊 You've made **{pred_count}** predictions! You're becoming a real estate expert!"
    elif pred_count > 0:
        return f"📈 You've made **{pred_count}** prediction{'s' if pred_count > 1 else ''}. Keep exploring to discover market trends!"
    return "💡 New here? Start making predictions to get personalized investment advice!"

def generate_roi_analysis():
    """Generate ROI calculator for upgrades"""
    return """🧮 **Upgrade ROI Calculator:**

| Upgrade | Cost | Rent Increase | Payback Period |
|---------|------|---------------|----------------|
| +1 Bedroom | ₹5,00,000 | +10-15% | 8-10 years |
| +1 Bathroom | ₹3,00,000 | +5-8% | 10-12 years |
| Fully Furnished | ₹2,50,000 | +15-20% | 3-4 years |
| Premium Location | - | +18-25% | Immediate |

💡 **Best ROI:** Furnishing gives the fastest payback!
💡 Use the **'What-If'** tab to simulate your specific property!"""

def generate_response(message, df):
    """Enhanced response with city-specific answers"""
    msg = message.lower()
    cities_list = df['city'].unique().tolist()
    
    # ========== CITY-SPECIFIC MARKET OUTLOOK ==========
    # Check if user asked about a specific city's market outlook
    if any(word in msg for word in ['outlook', 'market trend', 'market outlook']):
        # Try to find a city mentioned
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_market_outlook(df, city)
                if result:
                    return result
        # If no specific city, return overall market outlook
        return get_overall_market_outlook(df)
    
    # ========== CITY-SPECIFIC INVESTMENT ANALYSIS ==========
    if any(word in msg for word in ['invest', 'roi', 'yield', 'investment', 'should i buy']):
        # Try to find a city mentioned
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_investment_analysis(df, city)
                if result:
                    return result
        
        # If city found via fuzzy matching
        city = fuzzy_match_city(msg, cities_list)
        if city:
            result = get_city_investment_analysis(df, city)
            if result:
                return result
        
        # Default investment info
        return get_overall_market_outlook(df)
    
    # ========== CITY COMPARISON ==========
    if any(word in msg for word in ['compare', 'vs', 'versus']):
        # Find two cities in the message
        mentioned_cities = []
        for city in cities_list:
            if city.lower() in msg:
                mentioned_cities.append(city)
        
        # Also check aliases
        for city in cities_list:
            if city.lower() in msg or any(alias in msg for alias in get_city_aliases(city)):
                if city not in mentioned_cities:
                    mentioned_cities.append(city)
        
        if len(mentioned_cities) >= 2:
            result = get_city_comparison(df, mentioned_cities[0], mentioned_cities[1])
            if result:
                return result
        
        return "💡 To compare cities, try: 'Compare Mumbai and Pune' or 'Compare Bangalore vs Chennai'"
    
    # ========== RENT PRICE FOR SPECIFIC CITY ==========
    if any(word in msg for word in ['rent', 'price', 'cost']):
        city = fuzzy_match_city(msg, cities_list)
        if city:
            city_data = get_city_data(df, city)
            if city_data:
                city_avg = df.groupby('city')['rent'].mean().sort_values()
                rank = list(city_avg.index).index(city) + 1
                total = len(city_avg)
                
                return f"""📊 **{city} Rent Analysis:**

• Average Rent: ₹{city_data['avg_rent']:,.0f}/month
• Price Range: ₹{city_data['min_rent']:,.0f} - ₹{city_data['max_rent']:,.0f}
• Based on {city_data['count']} properties
• Average Area: {city_data['avg_area']:.0f} sqft
• Average Bedrooms: {city_data['avg_beds']:.1f} BHK
• Price Rank: #{rank} out of {total} cities"""
    
    # ========== BEST DEAL / CHEAPEST CITY ==========
    if any(word in msg for word in ['best', 'cheapest', 'affordable', 'deal']):
        city_avg = df.groupby('city')['rent'].mean().sort_values()
        cheapest = city_avg.index[0]
        cheapest_price = city_avg.iloc[0]
        second = city_avg.index[1] if len(city_avg) > 1 else None
        
        result = f"🏙️ **Best Deal Analysis:**\n\n🥇 **Most Affordable:** {cheapest} (₹{cheapest_price:,.0f}/month)"
        if second:
            result += f"\n🥈 **Second Best:** {second} (₹{city_avg.iloc[1]:,.0f}/month)"
        
        expensive = city_avg.index[-1]
        expensive_price = city_avg.iloc[-1]
        result += f"\n\n💡 You could save {((expensive_price - cheapest_price)/expensive_price*100):.0f}% by choosing {cheapest} over {expensive}!"
        
        return result
    
    # ========== NEGOTIATION TIPS ==========
    if any(word in msg for word in ['negotiate', 'offer', 'bargain']):
        return f"""🤝 **Smart Negotiation Strategies:**

{get_seasonal_insight()}

📋 **Key Tactics:**
• Start **8-12% below market rate**
• Mention how long the property has been listed
• Highlight comparable properties in the area
• Ask for concessions (repairs, furnishings, free parking)

💡 Use the **'Negotiation Assistant'** tab for personalized strategy!"""

    # ========== WHAT-IF / UPGRADE ROI ==========
    if any(word in msg for word in ['what if', 'upgrade', 'renovate']):
        return generate_roi_analysis()
    
    # ========== DEAL FINDER HELP ==========
    if any(word in msg for word in ['deal finder', 'find deals']):
        return """🎯 **Deal Finder Tab:**

• Finds properties **15%+ below market value**
• Shows discount percentage and savings
• Deal Score >70 = Excellent opportunity
• Color-coded badges: 🔥 HOT DEAL, 👍 GOOD DEAL, 📊 FAIR DEAL

💡 Click the **'Deals'** tab to see current discounts in your area!"""

    # ========== SMART COMPARE HELP ==========
    if any(word in msg for word in ['smart compare', 'compare properties']):
        return """⚖️ **Smart Compare Tab:**

• Compare **two properties** side by side
• See AI rent estimates for both
• Radar chart for visual comparison
• Get a **better value** recommendation

💡 Select cities, areas, and furnishing for each property!"""

    # ========== PROFILE TAB HELP ==========
    if any(word in msg for word in ['profile', 'my account', 'history']):
        pred_count = len(st.session_state.get('prediction_history', []))
        return f"""👤 **Profile Tab Features:**

📊 **Your Activity:** {pred_count} prediction{'s' if pred_count != 1 else ''}
📋 **Prediction History:** View all your past predictions
🔔 **Price Alerts:** Set and manage alerts
📄 **PDF Reports:** Download comprehensive valuation reports
📥 **Export Data:** Download your history as CSV

💡 Generate a **Professional PDF Report** to share with landlords!"""

    # ========== MY STATS ==========
    if 'my stats' in msg:
        return get_user_personalization()
    
    # ========== PREDICTION HELP ==========
    if any(word in msg for word in ['predict', 'how to predict']):
        return f"""🔮 **How to Predict Rent:**

1. Select a **City** from the sidebar dropdown
2. Enter the **Area** in square feet
3. Choose **Bedrooms, Bathrooms, Balconies**
4. Select **Furnishing** type
5. Click the **'Predict Rent'** button

The AI will analyze {len(df)} properties and give you an accurate estimate!"""

    # ========== SEASONAL INSIGHTS ==========
    if any(word in msg for word in ['season', 'best time']):
        return get_seasonal_insight()
    
    # ========== GREETING ==========
    if any(x in msg for x in ['hi', 'hello', 'hey']):
        return f"""👋 **Hello! I'm your AI Real Estate Expert.**

{get_user_personalization()}

📊 **I can help you with:**
• 💰 **Investment** - "Should I invest in Bangalore?"
• 📈 **Market Outlook** - "Market outlook for Pune"
• ⚖️ **Comparisons** - "Compare Mumbai and Delhi"
• 📊 **Rent Prices** - "Rent in Chennai"
• 🤝 **Negotiation** - "How to negotiate"
• 📚 **Tabs** - "How to use Profile tab"

🏙️ **Cities in my database:** {', '.join(cities_list[:5])}{'...' if len(cities_list) > 5 else ''}

What would you like to know?"""

    # ========== THANK YOU ==========
    if 'thank' in msg:
        return "You're very welcome! 😊 I'm here to help with all your real estate decisions. Feel free to ask anything else!"

    # ========== HELP ==========
    if 'help' in msg:
        return f"""💡 **Try these queries:**

• "Rent in Mumbai" - Get current rent prices
• "Compare Bangalore and Pune" - City comparison
• "Should I invest in Hyderabad?" - Investment analysis
• "Market outlook for Chennai" - City-specific trends
• "Best deal" - Most affordable cities
• "How to predict rent?" - Step-by-step guide

🏙️ **Cities covered:** {', '.join(cities_list[:4])}..."""

    # ========== DEFAULT ==========
    return f"""💡 **I can help with real estate queries!**

Try asking:
• "Rent in Mumbai" - Current rent prices
• "Compare Bangalore and Pune" - City comparison
• "Should I invest in Hyderabad?" - Investment analysis
• "Market outlook for Chennai" - City trends
• "Best deal" - Most affordable cities

🏙️ **Cities in my database:** {', '.join(cities_list[:5])}{'...' if len(cities_list) > 5 else ''}

What would you like to know about real estate?"""


def get_city_aliases(city_name):
    """Get common aliases for a city name"""
    aliases = {
        'Bangalore': ['bangalore', 'bengaluru', 'banglore'],
        'Mumbai': ['mumbai', 'bombay', 'mumbi'],
        'Delhi': ['delhi', 'new delhi', 'dilli'],
        'Chennai': ['chennai', 'madras', 'chenai'],
    }
    return aliases.get(city_name, [])


def floating_chatbot(df):
    """Native Streamlit floating chatbot with Logo Icon"""
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Expert. Ask me about rent prices, market outlook, or investment opportunities in any city!"}
        ]
    
    st.markdown("""
    <style>
    button[aria-label="Open popover"] {
        position: fixed;
        bottom: 25px;
        right: 25px;
        background: linear-gradient(135deg, #4f8df5, #6c5ce7) !important;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        z-index: 999;
        box-shadow: 0 4px 15px rgba(79,141,245,0.4);
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
    }
    
    button[aria-label="Open popover"]::after {
        content: "🤖";
        font-size: 30px;
        line-height: 1;
    }
    
    button[aria-label="Open popover"] > div {
        display: none !important;
    }
    
    button[aria-label="Open popover"]:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 20px rgba(79,141,245,0.6);
    }
    
    div[role="dialog"] {
        width: 400px !important;
        max-width: 90vw !important;
        border-radius: 16px !important;
        border: 1px solid #4f8df5 !important;
        background: #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.popover("", use_container_width=False):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-size: 28px;">🤖</span>
            <h3 style="margin: 0; color: white;">AI Real Estate Expert</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("*Get city-specific insights, investment analysis, and market trends*")
        st.markdown("---")
        
        chat_container = st.container(height=380)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        if prompt := st.chat_input("Ask about a city or real estate topic..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            response = generate_response(prompt, df)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Expert. Ask me about rent prices, market outlook, or investment opportunities in any city!"}
            ]
            st.rerun()


def inject_chat_widget(df):
    """Main function to call from app.py"""
    floating_chatbot(df)
