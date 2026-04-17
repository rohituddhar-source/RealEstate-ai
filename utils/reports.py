# utils/reports.py
from fpdf import FPDF
import datetime
import pandas as pd
import streamlit as st
import re

def clean_text(text):
    """Remove or replace special characters"""
    if text is None:
        return ""
    text = str(text)
    # Replace common emojis with text
    emoji_map = {
        '📋': '[Info]', '🏠': '[Property]', '💰': '[Money]', '📊': '[Chart]',
        '🔑': '[Key]', '👤': '[User]', '📧': '[Email]', '📅': '[Date]',
        '🕐': '[Time]', '✅': '[Success]', '⚠️': '[Warning]', '📍': '[Location]',
        '🛏️': '[Bed]', '🚽': '[Bath]', '🌅': '[Balcony]', '🪑': '[Furniture]',
        '⭐': '[Star]', '🔔': '[Alert]', '📈': '[Growth]', '📉': '[Decline]'
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    # Remove any remaining non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def create_comprehensive_report(city, rent, area, beds, baths, balconies, furn, 
                                 username, full_name, features_importance, financials):
    """Create a single comprehensive report combining valuation and investment analysis"""
    try:
        pdf = FPDF()
        
        # ========== PAGE 1: VALUATION REPORT ==========
        pdf.add_page()
        
        report_id = f"REAI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Header
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(79, 141, 245)
        pdf.cell(200, 15, txt="RealEstate AI Pro", ln=True, align='C')
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(200, 10, txt="Comprehensive Property Report", ln=True, align='C')
        pdf.ln(5)
        
        # Report ID and Date
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(100, 6, txt=f"Report ID: {report_id}", ln=0)
        pdf.cell(90, 6, txt=f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='R')
        pdf.ln(5)
        
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(8)
        
        # User Information
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 10, txt="Report Information", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(200, 8, txt=f"Prepared for: {clean_text(full_name)}", ln=True)
        pdf.cell(200, 8, txt=f"Username: @{clean_text(username)}", ln=True)
        pdf.cell(200, 8, txt=f"Report Type: Valuation & Investment Analysis", ln=True)
        pdf.ln(5)
        
        # Property Details
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Property Details", ln=True)
        pdf.set_font("Arial", '', 11)
        
        details = [
            ("City", clean_text(city)),
            ("Area", f"{area:,} sqft"),
            ("Bedrooms", str(beds)),
            ("Bathrooms", str(baths)),
            ("Balconies", str(balconies)),
            ("Furnishing", clean_text(furn))
        ]
        
        for label, value in details:
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(80, 8, txt=label, ln=0)
            pdf.set_font("Arial", '', 11)
            pdf.cell(100, 8, txt=value, ln=1)
        
        pdf.ln(5)
        
        # AI Valuation
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="AI Valuation Analysis", ln=True)
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(79, 141, 245)
        pdf.cell(200, 15, txt=f"Rs. {rent:,.2f}", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(200, 5, txt="Estimated Monthly Rent", ln=True, align='C')
        pdf.ln(8)
        
        # Market Comparison
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(200, 8, txt="Market Comparison", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 6, txt=f"* This property is valued at Rs. {rent:,.2f}/month", ln=True)
        pdf.cell(200, 6, txt=f"* Based on AI analysis of market trends in {clean_text(city)}", ln=True)
        pdf.cell(200, 6, txt=f"* Similar properties range between Rs. {rent*0.85:,.0f} - Rs. {rent*1.15:,.0f}", ln=True)
        
        # Key Price Drivers
        if features_importance is not None and not features_importance.empty:
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Key Price Drivers", ln=True)
            pdf.ln(3)
            
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(130, 8, txt="Factor", ln=0, fill=True)
            pdf.cell(50, 8, txt="Importance", ln=1, fill=True)
            
            pdf.set_font("Arial", '', 9)
            for _, row in features_importance.head(5).iterrows():
                feature_name = clean_text(row['feature'][:50])
                importance = f"{row['importance']*100:.1f}%"
                pdf.cell(130, 6, txt=feature_name, ln=0)
                pdf.cell(50, 6, txt=importance, ln=1)
        
        # Footer for Page 1
        pdf.set_y(-20)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, txt="This report was generated by RealEstate AI Pro", ln=True, align='C')
        pdf.cell(0, 5, txt=f"(c) 2026 RealEstate AI Pro | Report ID: {report_id} | Page 1", ln=True, align='C')
        
        # ========== PAGE 2: INVESTMENT ANALYSIS ==========
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(200, 10, txt="Investment Analysis", ln=True, fill=True)
        pdf.ln(5)
        
        # Financial Metrics Table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, txt="Financial Breakdown", ln=True)
        pdf.ln(3)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(100, 8, txt="Metric", ln=0, fill=True)
        pdf.cell(80, 8, txt="Value", ln=1, fill=True)
        
        pdf.set_font("Arial", '', 10)
        metrics = [
            ("Purchase Price", f"Rs. {financials['purchase_price']:,.0f}"),
            ("Down Payment (20%)", f"Rs. {financials['down_payment']:,.0f}"),
            ("Loan Amount", f"Rs. {financials['loan_amount']:,.0f}"),
            ("Interest Rate", f"{financials['interest_rate']:.1f}%"),
            ("Loan Tenure", f"{financials['loan_years']} years"),
            ("Monthly EMI", f"Rs. {financials['emi']:,.0f}"),
            ("Monthly Rent", f"Rs. {rent:,.0f}"),
            ("Annual Rental Income", f"Rs. {rent * 12:,.0f}"),
            ("Gross Yield", f"{financials['annual_yield']:.2f}%"),
            ("Cash-on-Cash ROI", f"{financials['roi']:.1f}%"),
            ("Cap Rate", f"{financials['cap_rate']:.1f}%"),
            ("Monthly Cash Flow", f"Rs. {financials.get('monthly_cash_flow', 0):,.0f}")
        ]
        
        for metric, value in metrics:
            pdf.cell(100, 7, txt=metric, ln=0)
            pdf.cell(80, 7, txt=value, ln=1)
        
        pdf.ln(8)
        
        # Investment Recommendation
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Investment Recommendation", ln=True)
        pdf.ln(3)
        
        pdf.set_font("Arial", '', 11)
        if financials['annual_yield'] > 8:
            pdf.set_text_color(0, 128, 0)
            pdf.cell(200, 8, txt="RECOMMENDED: Good Investment Opportunity", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 6, txt=f"* Gross yield of {financials['annual_yield']:.2f}% is above market average", ln=True)
            pdf.cell(200, 6, txt="* Positive cash flow expected", ln=True)
            pdf.cell(200, 6, txt="* Property has strong appreciation potential", ln=True)
        elif financials['annual_yield'] > 5:
            pdf.set_text_color(255, 140, 0)
            pdf.cell(200, 8, txt="CONSIDER: Moderate Investment Potential", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 6, txt=f"* Yield of {financials['annual_yield']:.2f}% is at market average", ln=True)
            pdf.cell(200, 6, txt="* Consider negotiating price for better returns", ln=True)
            pdf.cell(200, 6, txt="* Evaluate location growth potential", ln=True)
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.cell(200, 8, txt="CAUTION: Below Average Returns", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 6, txt=f"* Yield of {financials['annual_yield']:.2f}% is below market average", ln=True)
            pdf.cell(200, 6, txt="* Consider larger down payment or price negotiation", ln=True)
            pdf.cell(200, 6, txt="* Review property location and growth prospects", ln=True)
        
        pdf.ln(8)
        
        # Executive Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Executive Summary", ln=True)
        pdf.ln(3)
        
        pdf.set_font("Arial", '', 10)
        summary = [
            f"* Property: {beds} BHK in {clean_text(city)}, {area} sqft",
            f"* Estimated Monthly Rent: Rs. {rent:,.0f}",
            f"* Estimated Annual Rent: Rs. {rent * 12:,.0f}",
            f"* Purchase Price: Rs. {financials['purchase_price']:,.0f}",
            f"* Expected Gross Yield: {financials['annual_yield']:.1f}%",
            f"* Monthly Cash Flow: Rs. {financials.get('monthly_cash_flow', 0):,.0f}",
            f"* Investment Grade: {'A' if financials['annual_yield'] > 8 else 'B' if financials['annual_yield'] > 5 else 'C'}"
        ]
        
        for line in summary:
            pdf.cell(200, 6, txt=line, ln=True)
        
        # Footer for Page 2
        pdf.set_y(-20)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, txt="This report was generated by RealEstate AI Pro", ln=True, align='C')
        pdf.cell(0, 5, txt=f"(c) 2026 RealEstate AI Pro | Report ID: {report_id} | Page 2", ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        st.error(f"Error generating report: {e}")
        return None

def create_valuation_report(city, rent, area, beds, baths, balconies, furn, username, full_name, features_importance):
    """Legacy function - use create_comprehensive_report instead"""
    financials = {
        'purchase_price': int(rent * 200),
        'down_payment': int(rent * 200 * 0.2),
        'down_payment_pct': 20,
        'loan_amount': int(rent * 200 * 0.8),
        'interest_rate': 8.5,
        'loan_years': 20,
        'annual_yield': (rent * 12) / (rent * 200) * 100,
        'emi': int(rent * 200 * 0.8 * 0.008),
        'roi': ((rent * 12) / (rent * 200 * 0.2)) * 100,
        'cap_rate': ((rent * 12) / (rent * 200)) * 100,
        'monthly_cash_flow': (rent * 12 - (rent * 200 * 0.8 * 0.008 * 12)) / 12
    }
    return create_comprehensive_report(city, rent, area, beds, baths, balconies, furn, 
                                        username, full_name, features_importance, financials)

def create_investment_report(property_details, financials, username, full_name):
    """Legacy function - use create_comprehensive_report instead"""
    return create_comprehensive_report(
        city=property_details.get('city', 'Unknown'),
        rent=property_details.get('estimated_rent', property_details.get('rent', 0)),
        area=property_details.get('area', 0),
        beds=property_details.get('beds', 0),
        baths=property_details.get('baths', 0),
        balconies=property_details.get('balconies', 0),
        furn=property_details.get('furnishing', 'Unknown'),
        username=username,
        full_name=full_name,
        features_importance=pd.DataFrame(),
        financials=financials
    )