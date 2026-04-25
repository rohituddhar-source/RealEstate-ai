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

def extract_all_cities(query, cities_list):
    """Extract ALL cities mentioned in the query"""
    query_lower = query.lower()
    found_cities = []
    
    for city in cities_list:
        if city.lower() in query_lower:
            found_cities.append(city)
    
    # Also check aliases
    for alias, correct in {
        'bangalore': 'Bangalore', 'bengaluru': 'Bangalore', 'banglore': 'Bangalore',
        'mumbai': 'Mumbai', 'bombay': 'Mumbai', 'mumbi': 'Mumbai',
        'delhi': 'Delhi', 'new delhi': 'Delhi', 'dilli': 'Delhi',
        'chennai': 'Chennai', 'madras': 'Chennai', 'chenai': 'Chennai',
        'pune': 'Pune', 'poona': 'Pune',
        'nagpur': 'Nagpur', 'nagppur': 'Nagpur'
    }.items():
        if alias in query_lower and correct not in found_cities:
            found_cities.append(correct)
    
    return list(set(found_cities))

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
    """Get investment analysis for a specific city (text only)"""
    city_data = get_city_data(df, city)
    if not city_data:
        return None
    
    avg_rent = city_data['avg_rent']
    estimated_price = avg_rent * 200
    gross_yield = (avg_rent * 12 / estimated_price) * 100
    
    if gross_yield > 7:
        recommendation = "✅ GOOD INVESTMENT"
    elif gross_yield > 5:
        recommendation = "📊 MODERATE INVESTMENT"
    else:
        recommendation = "⚠️ CAUTION - Low Returns"
    
    return f"""💰 **Investment in {city}:**

📊 **Average Rent:** ₹{avg_rent:,.0f}/month
💰 **Est. Property Price:** ₹{estimated_price:,.0f}
📈 **Gross Rental Yield:** {gross_yield:.1f}%

🎯 **Verdict:** {recommendation}

💡 Use the **'Investment'** tab for detailed EMI calculations!"""

def get_city_comparison_text(city1, city2, rent1, rent2):
    """Get text-only comparison between two cities"""
    diff = abs(rent1 - rent2)
    cheaper = city1 if rent1 < rent2 else city2
    pct_diff = (diff / max(rent1, rent2)) * 100
    
    return f"""⚖️ **{city1} vs {city2} Comparison:**

📊 **Rent Comparison:**
• {city1}: ₹{rent1:,.0f}/month
• {city2}: ₹{rent2:,.0f}/month
• {cheaper} is **{pct_diff:.0f}% cheaper** (save ₹{diff:,.0f}/month)

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

def generate_available_cities_list(df, exclude_city=None):
    """Generate a formatted list of available cities for comparison"""
    cities = df['city'].unique().tolist()
    if exclude_city and exclude_city in cities:
        cities = [c for c in cities if c != exclude_city]
    
    if len(cities) <= 4:
        return ", ".join(cities)
    else:
        return ", ".join(cities[:4]) + f" and {len(cities)-4} more"


def generate_follow_up(context, last_city, df):
    """Generate contextual follow-up questions based on conversation history"""
    follow_ups = []
    
    if context == "after_rent":
        follow_ups = [
            f"📊 Compare {last_city} with another city",
            f"💰 Investment opportunities in {last_city}",
            f"🏙️ Market outlook for {last_city}",
            f"🛏️ What if I add a bedroom in {last_city}?"
        ]
    elif context == "after_comparison":
        follow_ups = [
            f"💰 Which city has better investment returns?",
            f"🏙️ Market outlook for the cheaper city",
            f"🛏️ Upgrade impact on rent",
            f"📊 Compare with one more city"
        ]
    elif context == "after_investment":
        follow_ups = [
            f"🏙️ Best city for rental income",
            f"📈 5-year wealth projection",
            f"🏠 Should I buy or rent?",
            f"📍 Which area has highest appreciation?"
        ]
    elif context == "after_upgrade":
        follow_ups = [
            f"💰 Compare returns with different upgrade",
            f"🏙️ Best city for rental property",
            f"📊 Market trends in {last_city}",
            f"🤝 How to negotiate rent?"
        ]
    else:
        follow_ups = [
            f"📊 Check rent in {last_city}",
            f"💰 Investment in {last_city}",
            f"⚖️ Compare {last_city} with Mumbai",
            f"🏆 Find best deal city"
        ]
    
    return follow_ups[:3]


def generate_response(message, df, conversation_stage, conversation_context):
    """Enhanced response with continuous conversation flow"""
    sentiment, prefix = analyze_sentiment(message)
    msg = message.lower().strip()
    cities_list = df['city'].unique().tolist()
    all_rents = df['rent']
    
    # ========== CONTINUOUS FOLLOW-UP BASED ON CONTEXT ==========
    
    # Stage 1: After showing rent, asking for comparison
    if conversation_stage == "awaiting_comparison_decision":
        if msg in ['yes', 'yeah', 'sure', 'yep', 'ok', 'okay']:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                available_cities = generate_available_cities_list(df, last_city)
                result = f"Great! Which city would you like to compare with **{last_city}**? I have data for: {available_cities}\n\nJust type the city name."
                return result, "awaiting_comparison_city", "after_rent"
        elif msg in ['no', 'nope', 'nah', 'not']:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                result = f"Okay! Would you like to know about investment opportunities in **{last_city}**? (Say 'yes' or 'no')"
                return result, "awaiting_investment_decision", "after_rent"
        else:
            comparison_city = smart_city_detection(message, df)
            if comparison_city:
                last_city = st.session_state.get("last_rent_city", None)
                if last_city and comparison_city != last_city:
                    data1 = get_city_data(df, last_city)
                    data2 = get_city_data(df, comparison_city)
                    if data1 and data2:
                        rent1 = data1['avg_rent']
                        rent2 = data2['avg_rent']
                        result = get_city_comparison_text(last_city, comparison_city, rent1, rent2)
                        # Ask follow-up after comparison
                        follow_up = "\n\n💡 **What would you like to do next?**\n• Say 'yes' to explore upgrades\n• Say 'investment' for financial analysis\n• Or ask about another city"
                        return result + follow_up, "awaiting_further_action", "after_comparison"
            last_city = st.session_state.get("last_rent_city", "Pune")
            result = f"I didn't understand. Would you like to compare **{last_city}** with another city? (Say 'yes' or 'no')"
            return result, "awaiting_comparison_decision", conversation_context
    
    # Stage 2: Waiting for comparison city name
    if conversation_stage == "awaiting_comparison_city":
        comparison_city = smart_city_detection(message, df)
        if comparison_city:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city and comparison_city != last_city:
                data1 = get_city_data(df, last_city)
                data2 = get_city_data(df, comparison_city)
                if data1 and data2:
                    rent1 = data1['avg_rent']
                    rent2 = data2['avg_rent']
                    result = get_city_comparison_text(last_city, comparison_city, rent1, rent2) + "\n\n💡 **Want to explore more?**\n• Say 'upgrade' to see renovation ROI\n• Say 'investment' for financial analysis\n• Or ask about another city"
                    return result, "awaiting_further_action", "after_comparison"
        result = f"I couldn't recognize that city. Please try another city name, or say 'no' to stop."
        return result, "awaiting_comparison_city", conversation_context
    
    # Stage 3: After comparison or investment, ask for next action
    if conversation_stage == "awaiting_further_action":
        if 'upgrade' in msg or 'bedroom' in msg or 'bathroom' in msg or 'furnish' in msg:
            last_city = st.session_state.get("last_rent_city", None)
            result = f"Great! Let me help with upgrades in **{last_city}**.\n\n**Upgrade ROI Calculator:**\n\n• 🛏️ Adding a bedroom: +10-15% rent (8-10 years payback)\n• 🚽 Adding a bathroom: +5-8% rent (10-12 years payback)\n• 🪑 Fully furnished: +15-20% rent (3-4 years payback)\n• ⭐ Premium location: +18-25% rent (immediate)\n\n💡 **What would you like to know next?**\n• Say 'compare' to compare with another city\n• Say 'investment' for financial analysis\n• Or ask about market trends"
            return result, "awaiting_further_action", "after_upgrade"
        
        elif 'investment' in msg or 'roi' in msg or 'yield' in msg:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                result = get_city_investment_analysis(df, last_city) + "\n\n💡 **Explore more:**\n• Say 'upgrade' to see renovation ROI\n• Say 'market' for current trends\n• Or ask 'best deal' for affordable cities"
                return result, "awaiting_further_action", "after_investment"
        
        elif 'market' in msg or 'trend' in msg or 'outlook' in msg:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                result = get_city_market_outlook(df, last_city) + "\n\n💡 **Want to continue?**\n• Say 'investment' for ROI analysis\n• Say 'compare' to compare with another city\n• Or ask 'best deal'"
                return result, "awaiting_further_action", "after_market"
        
        elif 'compare' in msg:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                available_cities = generate_available_cities_list(df, last_city)
                result = f"Which city would you like to compare with **{last_city}**? I have data for: {available_cities}\n\nJust type the city name."
                return result, "awaiting_comparison_city", "after_rent"
        
        elif 'best' in msg or 'deal' in msg or 'cheapest' in msg:
            city_avg = df.groupby('city')['rent'].mean().sort_values()
            cheapest = city_avg.index[0]
            cheapest_price = city_avg.iloc[0]
            result = f"🏙️ **Best Deal:** 🥇 **{cheapest}** is the most affordable city at **₹{cheapest_price:,.0f}/month**!\n\n💡 Would you like to see investment opportunities in **{cheapest}**? (Say 'yes' or 'no')"
            st.session_state.last_rent_city = cheapest
            return result, "awaiting_investment_decision", "after_best_deal"
        
        elif msg in ['yes', 'yeah', 'sure', 'yep']:
            # Continue with more suggestions
            last_city = st.session_state.get("last_rent_city", None)
            follow_ups = generate_follow_up(conversation_context, last_city, df)
            follow_up_text = "\n\n".join([f"• {f}" for f in follow_ups])
            result = f"Great! Here are some things you can explore:\n\n{follow_up_text}\n\nJust type what interests you!"
            return result, "awaiting_further_action", conversation_context
        
        elif msg in ['no', 'nope', 'nah', 'not']:
            result = "No problem! Feel free to ask me about rent prices, comparisons, or investment opportunities anytime.\n\nTry: 'Rent in Mumbai' or 'Best deal'"
            return result, "normal", "normal"
        
        else:
            # Check if user mentioned another city
            new_city = smart_city_detection(message, df)
            if new_city and new_city != st.session_state.get("last_rent_city"):
                st.session_state.last_rent_city = new_city
                data = get_city_data(df, new_city)
                if data:
                    price_level, level_name, price_color = get_price_level(data['avg_rent'], all_rents)
                    rent_meter = create_rent_meter(new_city, data['avg_rent'], data['min_rent'], data['max_rent'], data['avg_area'], data['avg_beds'], price_level, price_color)
                    result = rent_meter + "\n\n💡 **Would you like to compare this city with another?** (Say 'yes' or 'no')"
                    return result, "awaiting_comparison_decision", "after_rent"
            
            # Default: show available options
            last_city = st.session_state.get("last_rent_city", "Pune")
            result = f"I can help you with:\n• Compare {last_city} with another city\n• Investment analysis for {last_city}\n• Market outlook\n• Best deals\n\nWhat would you like to explore?"
            return result, "awaiting_further_action", conversation_context
    
    # Stage 4: Investment decision
    if conversation_stage == "awaiting_investment_decision":
        if msg in ['yes', 'yeah', 'sure', 'yep']:
            last_city = st.session_state.get("last_rent_city", None)
            if last_city:
                result = get_city_investment_analysis(df, last_city) + "\n\n💡 **Want to explore more?**\n• Say 'upgrade' to see renovation ROI\n• Say 'compare' to compare with another city\n• Or ask 'market' for trends"
                return result, "awaiting_further_action", "after_investment"
        elif msg in ['no', 'nope', 'nah', 'not']:
            result = "Okay! Would you like to compare cities or check market outlook? (Say 'compare' or 'market')"
            return result, "awaiting_further_action", "normal"
        else:
            last_city = st.session_state.get("last_rent_city", "Pune")
            result = f"Would you like to know about investment opportunities in **{last_city}**? (Say 'yes' or 'no')"
            return result, "awaiting_investment_decision", conversation_context
    
    # ========== INITIAL QUERIES ==========
    
    # Extract all cities from query
    mentioned_cities = extract_all_cities(msg, cities_list)
    
    # Check for direct comparison (2+ cities mentioned)
    if len(mentioned_cities) >= 2:
        city1, city2 = mentioned_cities[0], mentioned_cities[1]
        data1 = get_city_data(df, city1)
        data2 = get_city_data(df, city2)
        if data1 and data2:
            rent1 = data1['avg_rent']
            rent2 = data2['avg_rent']
            result = get_city_comparison_text(city1, city2, rent1, rent2) + "\n\n💡 **What would you like to do next?**\n• Say 'upgrade' to see renovation ROI\n• Say 'investment' for financial analysis\n• Or ask about another city"
            st.session_state.last_rent_city = city1
            return result, "awaiting_further_action", "after_comparison"
    
    # Investment analysis
    if any(word in msg for word in ['invest', 'investment']):
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_investment_analysis(df, city) + "\n\n💡 **Explore more:**\n• Say 'upgrade' to see renovation ROI\n• Say 'compare' to compare with another city\n• Or ask 'market' for trends"
                st.session_state.last_rent_city = city
                return result, "awaiting_further_action", "after_investment"
        city = smart_city_detection(message, df)
        if city:
            result = get_city_investment_analysis(df, city) + "\n\n💡 **Explore more:**\n• Say 'upgrade' to see renovation ROI\n• Say 'compare' to compare with another city"
            st.session_state.last_rent_city = city
            return result, "awaiting_further_action", "after_investment"
    
    # Rent price with meter
    if any(word in msg for word in ['rent', 'price']):
        city = smart_city_detection(message, df)
        if city:
            data = get_city_data(df, city)
            if data:
                st.session_state.last_rent_city = city
                st.session_state.conversation_stage = "awaiting_comparison_decision"
                st.session_state.conversation_context = "after_rent"
                
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
                
                follow_up_text = f"\n\n💡 **Would you like to compare {city} with another city?**\n*(Say 'yes' to compare, 'no' for investment options, or type a city name directly)*"
                
                return rent_meter + follow_up_text, "awaiting_comparison_decision", "after_rent"
        result = f"Which city's rent would you like to see? Try 'Rent in Mumbai' or 'Rent in Pune'"
        return result, "normal", "normal"
    
    # Best deal
    if any(word in msg for word in ['best', 'cheapest', 'deal']):
        city_avg = df.groupby('city')['rent'].mean().sort_values()
        cheapest = city_avg.index[0]
        cheapest_price = city_avg.iloc[0]
        
        st.session_state.last_rent_city = cheapest
        result = f"🏙️ **Best Deal:** 🥇 **{cheapest}** is the most affordable city at **₹{cheapest_price:,.0f}/month**!\n\n💡 Would you like to see investment opportunities in **{cheapest}**? (Say 'yes' or 'no')"
        return result, "awaiting_investment_decision", "after_best_deal"
    
    # Market outlook
    if any(word in msg for word in ['outlook', 'market']):
        for city in cities_list:
            if city.lower() in msg:
                result = get_city_market_outlook(df, city) + "\n\n💡 **Want to continue?**\n• Say 'investment' for ROI analysis\n• Say 'compare' to compare with another city"
                st.session_state.last_rent_city = city
                return result, "awaiting_further_action", "after_market"
        city = smart_city_detection(message, df)
        if city:
            result = get_city_market_outlook(df, city) + "\n\n💡 **Want to continue?**\n• Say 'investment' for ROI analysis\n• Say 'compare' to compare with another city"
            st.session_state.last_rent_city = city
            return result, "awaiting_further_action", "after_market"
        result = get_overall_market_outlook(df)
        return result, "normal", "normal"
    
    # Negotiation tips
    if any(word in msg for word in ['negotiate', 'offer']):
        result = f"""🤝 **Negotiation Tips:**

{get_seasonal_insight()}
• Start 8-12% below market rate
• Mention how long property has been listed
• Ask for small repairs or free parking

💡 Would you like to know about current market trends? (Say 'market')"""
        return result, "awaiting_further_action", "after_negotiation"
    
    # My stats
    if 'my stats' in msg:
        result = get_user_personalization() + "\n\n💡 Want to make more predictions? Use the sidebar to predict rent!"
        return result, "normal", "normal"
    
    # Upgrade/What-if
    if any(word in msg for word in ['what if', 'upgrade', 'add']):
        last_city = st.session_state.get("last_rent_city", "Pune")
        result = f"🧮 **Upgrade ROI Calculator for {last_city}:**\n\n• 🛏️ Adding a bedroom: +10-15% rent (8-10 years payback)\n• 🚽 Adding a bathroom: +5-8% rent (10-12 years payback)\n• 🪑 Fully furnished: +15-20% rent (3-4 years payback)\n• ⭐ Premium location: +18-25% rent (immediate)\n\n💡 **What would you like to know next?**\n• Say 'investment' for financial analysis\n• Say 'compare' to compare with another city"
        return result, "awaiting_further_action", "after_upgrade"
    
    # Help
    if msg == 'help':
        result = """💡 **Available Commands:**
• "Rent in Mumbai" - See rent with visual meter
• "Compare Mumbai and Pune" - Compare two cities
• "Investment in Pune" - Investment analysis
• "Best deal" - Find cheapest city
• "Market outlook" - Current trends
• "Upgrade" - Renovation ROI calculator
• "Negotiation tips" - How to negotiate

💡 The chatbot will keep suggesting follow-up questions - just type 'yes' or your choice!"""
        return result, "normal", "normal"
    
    # Greeting
    if any(x in msg for x in ['hi', 'hello', 'hey']):
        rec = get_personalized_recommendations(df)
        rec_text = f"\n\n{rec}" if rec else ""
        result = f"""👋 **Hello! I'm your AI Real Estate Assistant.**

{get_user_personalization()}{rec_text}

💡 **Try these commands:**
• "Rent in Mumbai" - See rent meter
• "Compare Mumbai and Pune" - Compare cities
• "Investment in Pune" - Investment analysis
• "Best deal" - Find cheapest city

I'll keep suggesting follow-up questions - just say 'yes' or type what interests you!
Type 'help' for all commands"""
        return result, "normal", "normal"
    
    if 'thank' in msg:
        result = "You're welcome! 😊 Happy to help! Is there anything else about real estate you'd like to know?"
        return result, "awaiting_further_action", "normal"
    
    # Default response with continuous engagement
    last_city = st.session_state.get("last_rent_city", "Pune")
    result = f"""💡 **Here's what I can help with:**

• 📊 Check rent in **{last_city}**
• ⚖️ Compare **{last_city}** with another city
• 💰 Investment analysis for **{last_city}**
• 🏆 Find the best deal city
• 🛏️ Upgrade ROI calculator

Just type what you're interested in! (e.g., 'compare', 'investment', 'upgrade')

Type 'help' for all commands"""
    return result, "awaiting_further_action", "normal"


def analyze_sentiment(text):
    """Simple sentiment analysis"""
    positive_words = ['good', 'great', 'excellent', 'awesome', 'love', 'perfect', 'thanks', 'thank']
    negative_words = ['bad', 'poor', 'expensive', 'worried', 'concerned']
    
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
    """Natural conversational floating chatbot with continuous flow"""
    
    # Initialize session state
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Assistant. Ask me about rent, investment, or best deals!"}
        ]
    
    if "last_response" not in st.session_state:
        st.session_state.last_response = ""
    
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    
    if "last_rent_city" not in st.session_state:
        st.session_state.last_rent_city = None
    
    if "conversation_stage" not in st.session_state:
        st.session_state.conversation_stage = "normal"
    
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = "normal"
    
    # CSS for floating button
    st.markdown("""
    <style>
    .floating-btn-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    
    .floating-chat-btn {
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #4f8df5, #6c5ce7);
        border-radius: 50%;
        border: none;
        box-shadow: 0 2px 10px rgba(79,141,245,0.3);
        cursor: pointer;
        transition: transform 0.2s;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .floating-chat-btn:hover {
        transform: scale(1.05);
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
    
    <div class="floating-btn-container">
        <button class="floating-chat-btn" id="floatingChatBtn">🤖</button>
    </div>
    
    <script>
    document.getElementById('floatingChatBtn').onclick = function() {
        var btn = document.querySelector('button[aria-label="Open popover"]');
        if (btn) btn.click();
    };
    </script>
    """, unsafe_allow_html=True)
    
    with st.popover("", use_container_width=False):
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="font-size: 20px;">🤖</span>
            <span style="font-weight: 600; color: white; font-size: 13px;">Assistant</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat history
        chat_container = st.container(height=380)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "assistant" and isinstance(msg.get("content"), str) and "<div style" in msg["content"]:
                        st.markdown(msg["content"], unsafe_allow_html=True)
                    else:
                        st.markdown(msg["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about real estate...", key="chat_input_field"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            response_text, new_stage, new_context = generate_response(
                prompt, df, 
                st.session_state.conversation_stage, 
                st.session_state.conversation_context
            )
            st.session_state.conversation_stage = new_stage
            st.session_state.conversation_context = new_context
            st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
            st.rerun()
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", key="clear_chat_btn", use_container_width=True):
                st.session_state.chat_messages = [
                    {"role": "assistant", "content": "👋 Hi! I'm your AI Real Estate Assistant. Ask me about rent, investment, or best deals!"}
                ]
                st.session_state.last_response = ""
                st.session_state.last_query = ""
                st.session_state.last_rent_city = None
                st.session_state.conversation_stage = "normal"
                st.session_state.conversation_context = "normal"
                st.rerun()
        with col2:
            export_chat_history()


def inject_chat_widget(df):
    """Main function to call from app.py"""
    floating_chatbot(df)
