# utils/chatbot.py
import streamlit as st
import pandas as pd
import difflib
from datetime import datetime
import random

def fuzzy_match_city(user_input, cities_list):
    """Find closest matching city name even with typos"""
    user_input_lower = user_input.lower()
    
    # Handle special cases
    if 'new delhi' in user_input_lower or 'delhi' in user_input_lower:
        return 'Delhi'
    if 'mumbai' in user_input_lower or 'bombay' in user_input_lower:
        return 'Mumbai'
    if 'bangalore' in user_input_lower or 'bengaluru' in user_input_lower:
        return 'Bangalore'
    if 'chennai' in user_input_lower or 'madras' in user_input_lower:
        return 'Chennai'
    if 'pune' in user_input_lower:
        return 'Pune'
    if 'nagpur' in user_input_lower:
        return 'Nagpur' if 'Nagpur' in cities_list else None
    if 'hyderabad' in user_input_lower:
        return 'Hyderabad' if 'Hyderabad' in cities_list else None
    
    for city in cities_list:
        if city.lower() in user_input_lower:
            return city
    
    matches = difflib.get_close_matches(user_input_lower, [c.lower() for c in cities_list], n=1, cutoff=0.6)
    if matches:
        for city in cities_list:
            if city.lower() == matches[0]:
                return city
    
    return None

def get_city_data(df, city):
    """Get comprehensive data for a city"""
    city_data = df[df['city'] == city]
    if city_data.empty:
        return None
    
    return {
        'avg_rent': city_data['rent'].mean(),
        'min_rent': city_data['rent'].min(),
        'max_rent': city_data['rent'].max(),
        'median_rent': city_data['rent'].median(),
        'std_rent': city_data['rent'].std(),
        'count': len(city_data),
        'avg_area': city_data['area'].mean(),
        'avg_beds': city_data['beds'].mean()
    }

def calculate_investment_score(city_data, city_name):
    """Calculate 0-100 investment score with recommendation"""
    avg_rent = city_data['avg_rent']
    estimated_price = avg_rent * 200
    gross_yield = (avg_rent * 12 / estimated_price) * 100
    
    affordability = max(0, min(100, 100 - (avg_rent / 100000 * 100)))
    value_score = min(100, (avg_rent / city_data['avg_area'] * 10)) if city_data['avg_area'] > 0 else 50
    
    growth_map = {
        'Mumbai': 75, 'Delhi': 70, 'Bangalore': 85, 'Pune': 80,
        'Chennai': 65, 'Hyderabad': 75, 'Kolkata': 55, 'Nagpur': 60
    }
    growth_potential = growth_map.get(city_name, 65)
    
    overall_score = (gross_yield * 5 + affordability * 2 + value_score * 2 + growth_potential) / 10
    overall_score = max(0, min(100, overall_score))
    
    if overall_score > 70:
        recommendation = "Strong Buy"
        risk_level = "Low"
    elif overall_score > 50:
        recommendation = "Consider"
        risk_level = "Medium"
    else:
        recommendation = "Hold"
        risk_level = "High"
    
    return {
        'overall_score': overall_score,
        'gross_yield': gross_yield,
        'affordability': affordability,
        'value_score': value_score,
        'growth_potential': growth_potential,
        'recommendation': recommendation,
        'risk_level': risk_level
    }

def get_seasonal_insight():
    """Provide seasonal real estate insights"""
    month = datetime.now().month
    if month in [11, 12, 1, 2]:
        return "❄️ **Winter Season (Nov-Feb):** Lower demand, better negotiation power. You can get 5-10% discounts!"
    elif month in [3, 4, 5]:
        return "🌸 **Spring Season (Mar-May):** High demand, prices tend to rise. Act fast on good deals!"
    else:
        return "☀️ **Summer/Fall (Jun-Oct):** Moderate market. Good time for long-term investments."

def get_user_personalization(df):
    """Get personalized insights based on user's prediction history"""
    pred_count = len(st.session_state.get('prediction_history', []))
    
    fav_city = None
    if pred_count > 0:
        cities = [p.get('city', '') for p in st.session_state.prediction_history if p.get('city')]
        if cities:
            from collections import Counter
            fav_city = Counter(cities).most_common(1)[0][0]
    
    if pred_count > 10:
        return f"📊 **Power User!** You've made {pred_count} predictions. Your favorite city is {fav_city if fav_city else 'exploring various cities'}. Keep going!"
    elif pred_count > 0:
        return f"📈 **Active User:** You've made {pred_count} predictions. {f'You seem interested in {fav_city}!' if fav_city else 'Keep exploring!'}"
    return "💡 **New User:** Start making predictions to get personalized investment advice!"

def get_market_outlook(df):
    """Generate market outlook with hottest/cheapest cities"""
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    cheapest = city_avg.index[0]
    cheapest_price = city_avg.iloc[0]
    expensive = city_avg.index[-1]
    expensive_price = city_avg.iloc[-1]
    
    df['price_per_sqft'] = df['rent'] / df['area']
    best_value_city = df.groupby('city')['price_per_sqft'].mean().idxmin()
    
    return f"""📈 **Market Outlook:**

🔥 **Hottest Market:** {expensive} (₹{expensive_price:,.0f}/month)
💰 **Most Affordable:** {cheapest} (₹{cheapest_price:,.0f}/month)
⭐ **Best Value:** {best_value_city}

{get_seasonal_insight()}

💡 **Tip:** {cheapest} offers best entry point for first-time investors. You can save {(expensive_price - cheapest_price)/expensive_price*100:.0f}% compared to {expensive}!"""

def generate_roi_analysis():
    """Generate ROI calculator for upgrades"""
    return """🧮 **Upgrade ROI Calculator:**

| Upgrade | Cost | Rent Increase | Monthly Gain | Payback Period |
|---------|------|---------------|--------------|----------------|
| +1 Bedroom | ₹5,00,000 | +12% | ₹4,800 | 8.7 years |
| +1 Bathroom | ₹3,00,000 | +6% | ₹2,400 | 10.4 years |
| +1 Balcony | ₹1,50,000 | +3% | ₹1,200 | 10.4 years |
| Fully Furnished | ₹2,50,000 | +15% | ₹6,000 | 3.5 years |
| Premium Location | - | +20% | ₹8,000 | Immediate |

💡 **Best ROI:** Furnishing gives fastest payback (3.5 years)!
💡 Use **'What-If'** tab to simulate your specific property!"""

def generate_response(message, df):
    """Enhanced response with ALL features"""
    msg = message.lower()
    cities_list = df['city'].unique().tolist()
    
    if any(word in msg for word in ['outlook', 'market trend', 'overview', 'market outlook']):
        return get_market_outlook(df)
    
    if any(word in msg for word in ['invest', 'roi', 'yield', 'return', 'buy', 'purchase', 'should i', 'investment score']):
        city = fuzzy_match_city(msg, cities_list)
        if city:
            city_data = get_city_data(df, city)
            if city_data:
                score_data = calculate_investment_score(city_data, city)
                return f"""💰 **Investment Analysis for {city}:** (Score: {score_data['overall_score']:.0f}/100)

📊 **Key Metrics:**
• Gross Yield: {score_data['gross_yield']:.1f}%
• Affordability: {score_data['affordability']:.0f}/100
• Value Score: {score_data['value_score']:.0f}/100
• Growth Potential: {score_data['growth_potential']:.0f}/100

🎯 **Recommendation:** {score_data['recommendation']}
⚠️ **Risk Level:** {score_data['risk_level']}

💡 Use **'Investment'** tab for detailed EMI and cash flow analysis!"""
        return get_market_outlook(df)
    
    if any(word in msg for word in ['compare', 'vs', 'versus', 'difference', 'cheaper', 'expensive']):
        mentioned_cities = []
        for city in cities_list:
            if city.lower() in msg:
                mentioned_cities.append(city)
        
        special = ['delhi', 'mumbai', 'bangalore', 'chennai', 'pune', 'nagpur', 'hyderabad']
        for sc in special:
            if sc in msg and sc.title() not in mentioned_cities and sc.title() in cities_list:
                mentioned_cities.append(sc.title())
        
        mentioned_cities = list(set(mentioned_cities))
        
        if len(mentioned_cities) >= 2:
            c1, c2 = mentioned_cities[0], mentioned_cities[1]
            data1 = get_city_data(df, c1)
            data2 = get_city_data(df, c2)
            
            if data1 and data2:
                score1 = calculate_investment_score(data1, c1)
                score2 = calculate_investment_score(data2, c2)
                rent1 = data1['avg_rent']
                rent2 = data2['avg_rent']
                diff = abs(rent1 - rent2)
                cheaper = c1 if rent1 < rent2 else c2
                pct_diff = (diff / max(rent1, rent2)) * 100
                
                return f"""⚖️ **{c1} vs {c2} Deep Analysis:**

📊 **Rent Comparison:**
• {c1}: ₹{rent1:,.0f}/month
• {c2}: ₹{rent2:,.0f}/month
• {cheaper} is **{pct_diff:.0f}% cheaper** (₹{diff:,.0f}/month savings)

📈 **Investment Scores:**
• {c1}: {score1['overall_score']:.0f}/100 ({score1['recommendation']})
• {c2}: {score2['overall_score']:.0f}/100 ({score2['recommendation']})

🏆 **Winner for Investment:** {c1 if score1['overall_score'] > score2['overall_score'] else c2}
💡 Use **'Smart Compare'** tab for detailed property comparison!"""
    
    if any(word in msg for word in ['roi', 'payback', 'upgrade cost', 'renovation payback']):
        return generate_roi_analysis()
    
    if any(word in msg for word in ['my stats', 'my activity', 'personal', 'my history']):
        return get_user_personalization(df)
    
    if any(word in msg for word in ['rent', 'price', 'cost', 'rate']):
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
    
    if any(word in msg for word in ['best', 'cheapest', 'affordable', 'deal', 'budget']):
        city_avg = df.groupby('city')['rent'].mean().sort_values()
        results = []
        for i, (city, rent) in enumerate(city_avg.items()):
            if i < 3:
                results.append(f"• {i+1}. **{city}**: ₹{rent:,.0f}/month")
        
        expensive = city_avg.index[-1]
        expensive_rent = city_avg.iloc[-1]
        
        return f"""🏙️ **Best Deal Analysis:**

**Most Affordable Cities:**
{chr(10).join(results)}

**Most Expensive:** {expensive} (₹{expensive_rent:,.0f}/month)

💡 **Save {((expensive_rent - city_avg.iloc[0])/expensive_rent*100):.0f}%** by choosing the cheapest city!

🎯 Check **'Deal Finder'** tab for 15%+ discounted properties!"""

    if any(word in msg for word in ['negotiate', 'offer', 'bargain', 'landlord']):
        return f"""🤝 **Smart Negotiation Strategies:**

{get_seasonal_insight()}

📋 **Key Tactics:**
• Start **8-12% below market rate**
• Mention **days on market** as leverage
• Highlight **comparable properties**
• Ask for **concessions** (repairs, furnishings, free parking)
• Get **pre-approved** to show seriousness

💡 Use **'Negotiation Assistant'** tab for personalized strategy!"""

    if any(word in msg for word in ['what if', 'upgrade', 'bedroom', 'bathroom', 'renovate']):
        return generate_roi_analysis()
    
    if any(word in msg for word in ['deal finder', 'find deals', 'discounted']):
        return """🎯 **Deal Finder Tab:**

• Finds properties **15%+ below market value**
• Shows discount percentage and savings
• Deal Score >70 = Excellent opportunity
• Color-coded badges: 🔥 HOT DEAL, 👍 GOOD DEAL, 📊 FAIR DEAL

💡 Click **'Deals'** tab to see current discounts in your area!"""

    if any(word in msg for word in ['smart compare', 'compare properties']):
        return """⚖️ **Smart Compare Tab:**

• Compare **two properties** side by side
• See rent estimates for both
• Radar chart for visual comparison
• Get **better value** recommendation

💡 Select cities, areas, and furnishing for each property!"""

    if any(word in msg for word in ['market', 'trend', 'distribution']):
        return get_market_outlook(df)
    
    if any(word in msg for word in ['profile', 'my account', 'history']):
        pred_count = len(st.session_state.get('prediction_history', []))
        fav_count = len(st.session_state.get('favorites', []))
        alert_count = len(st.session_state.get('alerts', []))
        return f"""👤 **Profile Tab Features:**

📊 **Your Stats:** {pred_count} predictions, {fav_count} favorites, {alert_count} alerts
📋 **Prediction History:** View all your past predictions
🔔 **Active Alerts:** Price alerts you've set
📄 **PDF Reports:** Download comprehensive valuation reports
📥 **Export Data:** Download your prediction history as CSV

💡 Generate a **Professional PDF Report** to share with landlords!"""

    if any(word in msg for word in ['predict', 'how to predict']):
        return f"""🔮 **How to Predict Rent:**

1. Select **City** from dropdown
2. Enter **Area** in sqft
3. Choose **Bedrooms, Bathrooms, Balconies**
4. Select **Furnishing** type
5. Click **'Predict Rent'** button

The AI will analyze {len(df)} properties and give you an accurate estimate!"""

    if any(word in msg for word in ['season', 'best time', 'when to buy']):
        return get_seasonal_insight()
    
    if any(x in msg for x in ['hi', 'hello', 'hey']):
        return f"""👋 **Hello! I'm your AI Real Estate Expert.**

{get_user_personalization(df)}

📊 **I can help you with:**
• 💰 **Investment Score** - "Should I invest in Pune?"
• 📈 **Market Outlook** - "Market outlook"
• ⚖️ **Deep Comparison** - "Compare Mumbai and Delhi"
• 🧮 **ROI Calculator** - "What if I add a bedroom?"
• 📊 **My Stats** - "My stats"
• 🤝 **Negotiation** - "How to negotiate"

🏙️ **Cities:** {', '.join(cities_list[:6])}...

What would you like to know?"""

    if 'thank' in msg:
        return "You're very welcome! 😊 I'm here to help with all your real estate decisions. Feel free to ask anything else!"

    return f"""💡 **Try these powerful queries:**

• "Market outlook" - Hottest/cheapest cities
• "Compare Mumbai and Delhi" - Deep analysis
• "Should I invest in Pune?" - Investment score
• "What if I add a bedroom?" - ROI calculator
• "My stats" - Personalized insights
• "How to negotiate" - Seasonal tactics

🏙️ **Cities:** {', '.join(cities_list[:5])}...

What would you like to know about real estate?"""


def floating_chatbot(df):
    """Native Streamlit floating chatbot with Logo Icon"""
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Expert. Ask me about investment scores, market outlook, or compare cities!"}
        ]
    
    # Updated CSS to focus on the Icon
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
    
    /* Adding the AI Robot Icon */
    button[aria-label="Open popover"]::after {
        content: "🤖";
        font-size: 30px;
        line-height: 1;
    }
    
    /* Removing default popover label padding */
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
    
    # Empty string for the label so only the icon shows via CSS
    with st.popover("", use_container_width=False):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-size: 28px;">🤖</span>
            <h3 style="margin: 0; color: white;">AI Real Estate Expert</h3>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("*Investment scores, market outlook, comparisons*")
        st.markdown("---")
        
        chat_container = st.container(height=380)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        if prompt := st.chat_input("Ask me anything..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            response = generate_response(prompt, df)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Expert. Ask me about investment scores, market outlook, or compare cities!"}
            ]
            st.rerun()


def inject_chat_widget(df):
    """Main function to call from app.py"""
    floating_chatbot(df)