# utils/chatbot.py
import streamlit as st
import pandas as pd
import difflib
from datetime import datetime
from collections import Counter
import plotly.express as px
import re
import time
import numpy as np

# ========== HELPER FUNCTIONS ==========

def fuzzy_match_city(user_input, cities_list):
    """Find closest matching city name even with typos"""
    user_input_lower = user_input.lower()
    
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
    
    for city in cities_list:
        if city.lower() in user_input_lower:
            return city
    
    matches = difflib.get_close_matches(user_input_lower, [c.lower() for c in cities_list], n=1, cutoff=0.6)
    if matches:
        for city in cities_list:
            if city.lower() == matches[0]:
                return city
    
    return None

def smart_city_detection(query, df):
    """Extract city even from complex sentences"""
    cities = df['city'].unique()
    query_lower = query.lower()
    
    for city in cities:
        if city.lower() in query_lower:
            return city
    
    patterns = [r'about\s+([A-Za-z]+)', r'in\s+([A-Za-z]+)', r'for\s+([A-Za-z]+)', r'at\s+([A-Za-z]+)']
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            potential = match.group(1).title()
            if potential in cities:
                return potential
    
    return fuzzy_match_city(query, cities)

def extract_city_mentioned(query):
    """Extract city name from query for context memory"""
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad', 'Nagpur', 'Kolkata']
    for city in cities:
        if city.lower() in query.lower():
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
        'count': len(city_data),
        'avg_area': city_data['area'].mean(),
        'avg_beds': city_data['beds'].mean()
    }

def get_price_level(avg_rent, all_rents):
    """Get simple price level indicator (₹ to ₹₹₹₹)"""
    if avg_rent <= all_rents.quantile(0.25):
        return "₹", "Budget Friendly", "#10b981"
    elif avg_rent <= all_rents.quantile(0.5):
        return "₹₹", "Moderate", "#f59e0b"
    elif avg_rent <= all_rents.quantile(0.75):
        return "₹₹₹", "Expensive", "#ef4444"
    else:
        return "₹₹₹₹", "Premium", "#8b5cf6"

def create_rent_meter(city, avg_rent, min_rent, max_rent, avg_area, avg_beds, price_level, price_color):
    """Create a simple rent meter visualization as HTML"""
    range_size = max_rent - min_rent
    if range_size > 0:
        position = ((avg_rent - min_rent) / range_size) * 100
    else:
        position = 50
    
    # Truncate position to 2 decimal places for cleaner display
    position = round(position, 1)
    
    return f"""
    <div style="background: #1e293b; border-radius: 12px; padding: 12px; margin: 10px 0; border-left: 4px solid {price_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 14px; font-weight: bold; color: white;">🏙️ {city}</span>
            <span style="background: {price_color}; padding: 2px 10px; border-radius: 20px; font-size: 11px; color: white;">{price_level}</span>
        </div>
        <div style="font-size: 20px; font-weight: bold; color: #4f8df5;">₹{avg_rent:,.0f}<span style="font-size: 12px; color: #94a3b8;">/month</span></div>
        <div style="margin: 8px 0;">
            <div style="background: #334155; border-radius: 10px; height: 8px; overflow: hidden;">
                <div style="width: {position}%; background: {price_color}; height: 100%; border-radius: 10px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                <span style="font-size: 10px; color: #94a3b8;">₹{min_rent:,.0f}</span>
                <span style="font-size: 10px; color: #94a3b8;">₹{max_rent:,.0f}</span>
            </div>
        </div>
        <div style="display: flex; gap: 15px; margin-top: 8px; font-size: 11px; color: #94a3b8;">
            <span>📐 {avg_area:.0f} sqft avg</span>
            <span>🛏️ {avg_beds:.1f} beds avg</span>
        </div>
    </div>
    """

def create_comparison_chart(city1, city2, rent1, rent2, price_level1, price_level2):
    """Create simple comparison bar chart as HTML"""
    max_rent = max(rent1, rent2)
    width1 = (rent1 / max_rent) * 100 if max_rent > 0 else 50
    width2 = (rent2 / max_rent) * 100 if max_rent > 0 else 50
    
    width1 = round(width1, 1)
    width2 = round(width2, 1)
    
    return f"""
    <div style="background: #1e293b; border-radius: 12px; padding: 15px; margin: 10px 0;">
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 13px; font-weight: bold; color: white;">{city1}</span>
                <span style="font-size: 13px; color: #4f8df5;">₹{rent1:,.0f}</span>
            </div>
            <div style="background: #334155; border-radius: 8px; height: 24px; overflow: hidden;">
                <div style="width: {width1}%; background: linear-gradient(90deg, #4f8df5, #6c5ce7); height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; color: white; font-size: 11px; font-weight: bold;">
                    {price_level1}
                </div>
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 13px; font-weight: bold; color: white;">{city2}</span>
                <span style="font-size: 13px; color: #a78bfa;">₹{rent2:,.0f}</span>
            </div>
            <div style="background: #334155; border-radius: 8px; height: 24px; overflow: hidden;">
                <div style="width: {width2}%; background: linear-gradient(90deg, #a78bfa, #c084fc); height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; color: white; font-size: 11px; font-weight: bold;">
                    {price_level2}
                </div>
            </div>
        </div>
        <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #334155; text-align: center;">
            <span style="font-size: 12px; color: #10b981;">💡 Save ₹{abs(rent1 - rent2):,.0f}/month by choosing the cheaper option!</span>
        </div>
    </div>
    """

def get_city_market_outlook(df, city):
    """Get market outlook for a specific city"""
    city_data = get_city_data(df, city)
    if not city_data:
        return None
    
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    rank = list(city_avg.index).index(city) + 1
    total_cities = len(city_avg)
    
    if rank <= total_cities // 3:
        position = "💰 Budget Friendly"
        advice = "Great for saving money"
    elif rank <= 2 * total_cities // 3:
        position = "📊 Mid-Range"
        advice = "Good value for money"
    else:
        position = "💎 Premium"
        advice = "Luxury living, higher cost"
    
    return f"""📈 **{city} Market Outlook:**

🏷️ **Category:** {position}
💰 **Avg Rent:** ₹{city_data['avg_rent']:,.0f}/month
📊 **Range:** ₹{city_data['min_rent']:,.0f} - ₹{city_data['max_rent']:,.0f}
💡 **Insight:** {advice}"""

def get_overall_market_outlook(df):
    """Generate overall market outlook"""
    city_avg = df.groupby('city')['rent'].mean().sort_values()
    cheapest = city_avg.index[0]
    cheapest_price = city_avg.iloc[0]
    expensive = city_avg.index[-1]
    expensive_price = city_avg.iloc[-1]
    
    return f"""📈 **Market Outlook:**

🔥 **Most Expensive:** {expensive} (₹{expensive_price:,.0f})
💰 **Most Affordable:** {cheapest} (₹{cheapest_price:,.0f})
💡 Save {((expensive_price - cheapest_price)/expensive_price*100):.0f}% by choosing {cheapest}!"""

def get_city_investment_analysis(df, city):
    """Get investment analysis for a specific city"""
    city_data = get_city_data(df, city)
    if not city_data:
        return None
    
    avg_rent = city_data['avg_rent']
    estimated_price = avg_rent * 200
    gross_yield = (avg_rent * 12 / estimated_price) * 100
    
    if gross_yield > 7:
        score = "High"
        recommendation = "✅ GOOD INVESTMENT"
        risk = "Low"
    elif gross_yield > 5:
        score = "Medium"
        recommendation = "📊 MODERATE"
        risk = "Medium"
    else:
        score = "Low"
        recommendation = "⚠️ CAUTION"
        risk = "High"
    
    return f"""💰 **Investment in {city}:**

📊 **Yield:** {gross_yield:.1f}%
📈 **Score:** {score} | **Risk:** {risk}
🎯 **Verdict:** {recommendation}"""

def get_city_comparison(df, city1, city2):
    """Get detailed comparison between two cities with visual chart"""
    data1 = get_city_data(df, city1)
    data2 = get_city_data(df, city2)
    
    if not data1 or not data2:
        return None
    
    rent1 = data1['avg_rent']
    rent2 = data2['avg_rent']
    diff = abs(rent1 - rent2)
    cheaper = city1 if rent1 < rent2 else city2
    pct_diff = (diff / max(rent1, rent2)) * 100
    
    # Get all rents for price level calculation
    all_rents = df['rent']
    price_level1, _, _ = get_price_level(rent1, all_rents)
    price_level2, _, _ = get_price_level(rent2, all_rents)
    
    # Create visual comparison chart
    comparison_chart = create_comparison_chart(city1, city2, rent1, rent2, price_level1, price_level2)
    
    return f"""⚖️ **{city1} vs {city2} Comparison:**

{comparison_chart}

📊 **Quick Facts:**
• {cheaper} is **{pct_diff:.0f}% cheaper**
• Save ₹{diff:,.0f} every month by choosing {cheaper}
• That's ₹{diff * 12:,.0f} savings per year!

💡 **Verdict:** {cheaper} is better for your wallet!"""

def get_seasonal_insight():
    """Provide seasonal real estate insights"""
    month = datetime.now().month
    if month in [11, 12, 1, 2]:
        return "❄️ Winter: Better negotiation (5-10% discounts)"
    elif month in [3, 4, 5]:
        return "🌸 Spring: High demand, prices rise"
    else:
        return "☀️ Summer/Fall: Moderate market"

def get_user_personalization():
    """Get personalized insights"""
    pred_count = len(st.session_state.get('prediction_history', []))
    if pred_count > 10:
        return f"📊 You've made {pred_count} predictions!"
    elif pred_count > 0:
        return f"📈 You've made {pred_count} prediction{'s' if pred_count > 1 else ''}"
    return "💡 Start predicting for personalized insights"

def get_personalized_recommendations(df):
    """Generate recommendations based on user's search history"""
    history = st.session_state.get('prediction_history', [])
    if not history:
        return None
    
    prices = [p['rent'] for p in history if 'rent' in p]
    if prices:
        avg_price = np.mean(prices)
        affordable_cities = df[df['rent'] < avg_price]['city'].unique()
        if len(affordable_cities) > 0:
            return f"🎯 You might like {', '.join(affordable_cities[:2])} - fits your budget"
    return None

def get_last_mentioned_city():
    """Get the last city mentioned in conversation from assistant responses"""
    for msg in reversed(st.session_state.chat_messages):
        if msg["role"] == "assistant":
            cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune', 'Hyderabad', 'Nagpur', 'Kolkata']
            for city in cities:
                if city in msg["content"]:
                    return city
    return None

def generate_available_cities_list(df, exclude_city=None):
    """Generate a formatted list of available cities for comparison"""
    cities = df['city'].unique().tolist()
    if exclude_city and exclude_city in cities:
        cities = [c for c in cities if c != exclude_city]
    
    if len(cities) <= 4:
        return ", ".join(cities)
    else:
        return ", ".join(cities[:4]) + f" and {len(cities)-4} more"


def generate_response(message, df):
    """Enhanced response with simple visualizations - returns tuple (text, html_content)"""
    sentiment, prefix = analyze_sentiment(message)
    msg = message.lower().strip()
    cities_list = df['city'].unique().tolist()
    all_rents = df['rent']
    
    # ========== CHECK FOR COMPARISON REQUEST ==========
    if st.session_state.get("awaiting_comparison_city", False) and msg not in ['yes', 'yeah', 'sure', 'no', 'nope']:
        comparison_city = smart_city_detection(message, df)
        if comparison_city:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city and comparison_city != last_city:
                result = get_city_comparison(df, last_city, comparison_city)
            else:
                other_city = None
                for city in cities_list:
                    if city != comparison_city:
                        other_city = city
                        break
                if other_city:
                    result = get_city_comparison(df, comparison_city, other_city)
                else:
                    result = "I need two different cities to compare."
            
            st.session_state.awaiting_comparison_city = False
            st.session_state.last_response = result
            return result, None
        else:
            available_cities = generate_available_cities_list(df, st.session_state.get("last_rent_city", None))
            result = f"I couldn't recognize that city name. Here are the cities I have data for: {available_cities}\n\nPlease tell me which city you'd like to compare with {st.session_state.get('last_rent_city', 'Pune')}."
            st.session_state.last_response = result
            return result, None
    
    # ========== HANDLE SIMPLE RESPONSES ==========
    if msg in ['yes', 'yeah', 'sure', 'yep']:
        if st.session_state.get("awaiting_comparison_city", False):
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                available_cities = generate_available_cities_list(df, last_city)
                result = f"Great! Which city would you like to compare with **{last_city}**? I have data for: {available_cities}\n\nJust type the city name."
                st.session_state.awaiting_comparison_city = True
                st.session_state.last_response = result
                return result, None
            else:
                result = "Which city would you like to compare? Try: Compare Mumbai and Pune"
                st.session_state.last_response = result
                return result, None
        else:
            result = "What would you like to know? Try asking about rent, investment, or market outlook in any city."
            st.session_state.last_response = result
            return result, None
    
    if msg in ['no', 'nope', 'nah', 'not']:
        if st.session_state.get("awaiting_comparison_city", False):
            st.session_state.awaiting_comparison_city = False
            result = "No problem! Let me know if you need help with anything else."
            st.session_state.last_response = result
            return result, None
        else:
            result = "Okay! Feel free to ask me about rent prices, investment, or market outlook in any city."
            st.session_state.last_response = result
            return result, None
    
    # ========== RENT PRICE WITH VISUAL METER ==========
    if any(word in msg for word in ['rent', 'price', 'cost']):
        city = smart_city_detection(message, df)
        if city:
            data = get_city_data(df, city)
            if data:
                st.session_state.last_rent_city = city
                st.session_state.awaiting_comparison_city = True
                
                # Create visual rent meter
                price_level, level_name, price_color = get_price_level(data['avg_rent'], all_rents)
                rent_meter = create_rent_meter(
                    city, 
                    data['avg_rent'], 
                    data['min_rent'], 
                    data['max_rent'],
                    data['avg_area'],
                    data['avg_beds'],
                    price_level, 
                    price_color
                )
                
                text_result = f"""📊 **{city} Rent Summary:**

💡 **Would you like to compare {city} with another city?** (Say 'yes' to compare or type a city name)

📌 **Price Level:** {level_name} ({price_level})"""
                
                st.session_state.last_response = text_result
                return text_result, rent_meter
    
    # ========== REGULAR INTENT DETECTION ==========
    
    # Market outlook
    if any(word in msg for word in ['outlook', 'market trend', 'market outlook']):
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_market_outlook(df, city)
                if result:
                    st.session_state.last_response = result
                    return result, None
        city = smart_city_detection(message, df)
        if city:
            result = get_city_market_outlook(df, city)
            if result:
                st.session_state.last_response = result
                return result, None
        result = get_overall_market_outlook(df)
        st.session_state.last_response = result
        return result, None
    
    # Investment
    if any(word in msg for word in ['invest', 'roi', 'yield', 'should i buy']):
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_investment_analysis(df, city)
                if result:
                    st.session_state.last_response = result
                    return result + "\n\n💡 Use the **Investment** tab for detailed EMI calculations!", None
        city = smart_city_detection(message, df)
        if city:
            result = get_city_investment_analysis(df, city)
            if result:
                st.session_state.last_response = result
                return result + "\n\n💡 Use the **Investment** tab for detailed EMI calculations!", None
        result = get_overall_market_outlook(df)
        st.session_state.last_response = result
        return result, None
    
    # Direct comparison
    if any(word in msg for word in ['compare', 'vs', 'versus']):
        mentioned = [c for c in cities_list if c.lower() in msg]
        if len(mentioned) >= 2:
            result = get_city_comparison(df, mentioned[0], mentioned[1])
            if result:
                st.session_state.awaiting_comparison_city = False
                st.session_state.last_response = result
                return result, None
        elif len(mentioned) == 1:
            available_cities = generate_available_cities_list(df, mentioned[0])
            result = f"Which city would you like to compare with **{mentioned[0]}**? I have data for: {available_cities}"
            st.session_state.awaiting_comparison_city = True
            st.session_state.last_rent_city = mentioned[0]
            st.session_state.last_response = result
            return result, None
        
        result = "To compare cities, try: 'Compare Mumbai and Pune' or 'Compare Bangalore vs Chennai'"
        st.session_state.last_response = result
        return result, None
    
    # Best deal
    if any(word in msg for word in ['best', 'cheapest', 'deal']):
        city_avg = df.groupby('city')['rent'].mean().sort_values()
        cheapest = city_avg.index[0]
        cheapest_price = city_avg.iloc[0]
        
        result = f"🏙️ **Best Deal:** 🥇 **{cheapest}** is the most affordable city at **₹{cheapest_price:,.0f}/month**!\n\n💡 Looking for budget-friendly options? {cheapest} is your best bet!"
        st.session_state.last_response = result
        return result, None
    
    # Negotiation
    if any(word in msg for word in ['negotiate', 'offer']):
        result = f"""🤝 **Negotiation Tips:**

{get_seasonal_insight()}
• Start 8-12% below market
• Mention how long property has been listed
• Ask for small repairs or free parking"""
        st.session_state.last_response = result
        return result, None
    
    # What-if
    if any(word in msg for word in ['what if', 'upgrade']):
        result = """🧮 **Upgrade ROI:**

| Upgrade | Cost | Rent Increase | Payback |
|---------|------|---------------|---------|
| +1 Bedroom | ₹5L | +10-15% | 8-10 years |
| +1 Bathroom | ₹3L | +5-8% | 10-12 years |
| Fully Furnished | ₹2.5L | +15-20% | 3-4 years |

💡 Best ROI: Furnishing pays back fastest!"""
        st.session_state.last_response = result
        return result, None
    
    # Profile stats
    if 'my stats' in msg:
        result = get_user_personalization()
        st.session_state.last_response = result
        return result, None
    
    # Greeting
    if any(x in msg for x in ['hi', 'hello', 'hey']):
        rec = get_personalized_recommendations(df)
        rec_text = f"\n\n{rec}" if rec else ""
        result = f"""👋 **Hello! I'm your AI Real Estate Expert.**

{get_user_personalization()}{rec_text}

📊 **Try these simple commands:**
• **"Rent in Mumbai"** - See rent with easy-to-read meter
• **"Compare Mumbai and Pune"** - Visual comparison chart
• **"Best deal"** - Find most affordable city
• **"Should I invest?"** - Quick investment advice

🏙️ **Cities:** {', '.join(cities_list[:4])}...

What would you like to know?"""
        st.session_state.last_response = result
        return result, None
    
    if 'thank' in msg:
        result = "You're welcome! 😊 Happy to help with your real estate decisions!"
        st.session_state.last_response = result
        return result, None
    
    if 'help' in msg:
        result = """💡 **Simple commands to try:**

• "Rent in Mumbai" - See rent with visual meter
• "Compare Mumbai and Pune" - Side-by-side comparison
• "Best deal" - Most affordable city
• "Should I invest in Bangalore?" - Investment advice
• "Market outlook" - Current trends"""
        st.session_state.last_response = result
        return result, None
    
    # Default response
    result = f"""💡 **Try these simple commands:**

• "Rent in Mumbai" - See rent with easy meter
• "Compare Mumbai and Pune" - Visual comparison
• "Best deal" - Find cheapest city
• "Should I invest in Bangalore?" - Investment advice

🏙️ **Cities:** {', '.join(cities_list[:5])}..."""
    st.session_state.last_response = result
    return result, None


def analyze_sentiment(text):
    """Simple sentiment analysis"""
    positive_words = ['good', 'great', 'excellent', 'awesome', 'love', 'perfect', 'thanks', 'thank']
    negative_words = ['bad', 'poor', 'expensive', 'worried', 'concerned', 'sad', 'terrible']
    
    text_lower = text.lower()
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        return "positive", "😊 "
    elif neg_count > pos_count:
        return "negative", "🤝 "
    return "neutral", ""


def export_chat_history():
    """Allow users to download chat history"""
    if st.button("📤", key="export_chat_btn", help="Export chat", use_container_width=True):
        if st.session_state.chat_messages:
            history_df = pd.DataFrame(st.session_state.chat_messages)
            csv = history_df.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_chat_btn"
            )
        else:
            st.toast("No chat history to export", icon="⚠️")


def floating_chatbot(df):
    """Minimal professional floating chatbot with simple visuals"""
    
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "👋 Hi! Ask me about rent, investment, or best deals!"}
        ]
    
    if "last_response" not in st.session_state:
        st.session_state.last_response = ""
    
    if "last_rent_city" not in st.session_state:
        st.session_state.last_rent_city = None
    
    if "awaiting_comparison_city" not in st.session_state:
        st.session_state.awaiting_comparison_city = False
    
    # Minimal CSS
    st.markdown("""
    <style>
    button[aria-label="Open popover"] {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #4f8df5, #6c5ce7) !important;
        border-radius: 50% !important;
        width: 50px !important;
        height: 50px !important;
        z-index: 999;
        box-shadow: 0 2px 10px rgba(79,141,245,0.3);
        border: none !important;
        padding: 0 !important;
    }
    
    button[aria-label="Open popover"]::after {
        content: "🤖";
        font-size: 24px;
        line-height: 1;
    }
    
    button[aria-label="Open popover"] > div {
        display: none !important;
    }
    
    div[role="dialog"] {
        width: 380px !important;
        max-width: 85vw !important;
        border-radius: 12px !important;
        background: #1e293b !important;
        border: 1px solid #334155 !important;
    }
    
    .stChatMessage {
        padding: 4px 0 !important;
    }
    
    .stChatMessage p {
        font-size: 12px !important;
        margin: 0 !important;
    }
    
    .stChatInput input {
        font-size: 12px !important;
        padding: 6px 10px !important;
    }
    
    .stButton button {
        font-size: 11px !important;
        padding: 4px 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.popover("", use_container_width=False):
        # Simple header
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 20px;">🤖</span>
            <span style="font-weight: 600; color: white; font-size: 13px;">AI Assistant</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat history
        chat_container = st.container(height=380)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    # Check if the message contains HTML content
                    if msg["role"] == "assistant" and isinstance(msg.get("content"), dict) and msg["content"].get("html"):
                        st.markdown(msg["content"]["text"])
                        st.markdown(msg["content"]["html"], unsafe_allow_html=True)
                    elif msg["role"] == "assistant" and isinstance(msg.get("content"), str):
                        # Check if it's a rent meter response (contains HTML)
                        if "<div style" in msg["content"]:
                            st.markdown(msg["content"], unsafe_allow_html=True)
                        else:
                            st.markdown(msg["content"])
                    else:
                        st.markdown(msg["content"])
        
        # Quick reply buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🏙️", key="qr_best", help="Best deal", use_container_width=True):
                query = "Best deal"
                st.session_state.chat_messages.append({"role": "user", "content": query})
                response_text, response_html = generate_response(query, df)
                if response_html:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_html})
                else:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
                st.rerun()
        with col2:
            if st.button("💰", key="qr_invest", help="Investment", use_container_width=True):
                query = "Should I invest in property?"
                st.session_state.chat_messages.append({"role": "user", "content": query})
                response_text, response_html = generate_response(query, df)
                if response_html:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_html})
                else:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
                st.rerun()
        with col3:
            if st.button("⚖️", key="qr_compare", help="Compare", use_container_width=True):
                query = "Compare Mumbai and Pune"
                st.session_state.chat_messages.append({"role": "user", "content": query})
                response_text, response_html = generate_response(query, df)
                if response_html:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_html})
                else:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
                st.rerun()
        with col4:
            if st.button("📊", key="qr_rent", help="Rent Meter", use_container_width=True):
                query = "Rent in Mumbai"
                st.session_state.chat_messages.append({"role": "user", "content": query})
                response_text, response_html = generate_response(query, df)
                if response_html:
                    # Store as dict with both text and HTML
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_html})
                else:
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
                st.rerun()
        
        # Chat input
        if prompt := st.chat_input("Ask...", key="chat_input_field"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            response_text, response_html = generate_response(prompt, df)
            if response_html:
                st.session_state.chat_messages.append({"role": "assistant", "content": response_html})
            else:
                st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
            st.rerun()
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️", key="clear_chat_btn", help="Clear chat", use_container_width=True):
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "👋 Hi! Ask me about rent, investment, or best deals!"}
                ]
                st.session_state.last_response = ""
                st.session_state.last_rent_city = None
                st.session_state.awaiting_comparison_city = False
                st.rerun()
        with col2:
            export_chat_history()


def inject_chat_widget(df):
    """Main function to call from app.py"""
    floating_chatbot(df)
