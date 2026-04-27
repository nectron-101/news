import streamlit as st
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="Google Trends Israel", layout="wide", page_icon="🔥")

# CSS "סקסי" - RTL מלא, כותרות לחיצות ועיצוב נקי ללא אקורדיון
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
        background-color: #f8f9fa;
    }
    
    .main-title {
        background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center !important;
        margin-bottom: 5px;
    }

    .data-status {
        text-align: center !important;
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 30px;
        font-weight: bold;
        color: #555;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
        border: 1px solid #eee;
    }

    .trend-card {
        background-color: #ffffff;
        border-right: 10px solid #4285F4;
        padding: 30px;
        margin-bottom: 35px;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }
    
    .item-title-link {
        color: #0056b3 !important;
        font-size: 2.5rem;
        font-weight: 800;
        text-decoration: none !important;
        transition: color 0.2s;
    }
    
    .item-title-link:hover {
        color: #ee3124 !important;
    }

    .traffic-badge {
        background: #e8f0fe;
        color: #1967d2;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 20px;
    }

    .news-box {
        margin-top: 20px;
        border-top: 1px solid #eee;
        padding-top: 20px;
    }

    .news-item {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 12px;
        background-color: #fcfcfc;
        border-radius: 8px;
        border: 1px solid #f1f1f1;
        margin-bottom: 10px;
        transition: background 0.2s;
    }

    .news-item:hover {
        background-color: #f8fbff;
    }

    .source-tag {
        background-color: #4285F4;
        color: white;
        padding: 3px 10px;
        border-radius: 5px;
        font-size: 0.75rem;
        font-weight: 800;
        min-width: 80px;
        text-align: center;
    }

    .date-tag {
        color: #999;
        font-size: 0.8rem;
        min-width: 50px;
    }

    .news-link {
        color: #333 !important;
        font-weight: 600;
        text-decoration: none !important;
        font-size: 1.1rem;
        flex-grow: 1;
    }

    .news-link:hover {
        color: #4285F4 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def fetch_trends():
    url = "https://trends.google.com/trending/rss?geo=IL"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        ns = {'ht': 'http://namespaces.google.com/trends/hottrends'}
        trends = []
        for item in root.findall('.//item'):
            title = item.find('title').text
            traffic = item.find('ht:approx_traffic', ns).text if item.find('ht:approx_traffic', ns) is not None else ""
            trends.append({'title': title, 'traffic': traffic})
        return trends[:20]
    except: return []

def get_news(query):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        news = []
        for item in root.findall('.//item')[:4]:
            full_title = item.find('title').text
            pub_date = item.find('pubDate').text
            try:
                date_str = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m')
            except: date_str = ""
            news.append({
                'title': full_title.split(" - ")[0] if " - " in full_title else full_title,
                'source': item.find('source').text if item.find('source') is not None else "חדשות",
                'link': item.find('link').text,
                'date': date_str
            })
        return news
    except: return []

# --- תצוגה ---
st.markdown('<h1 class="main-title">GOOGLE TRENDS ISRAEL</h1>', unsafe_allow_html=True)

trends_list = fetch_trends()

if trends_list:
    update_time = datetime.now().strftime('%H:%M - %d/%m/%Y')
    st.markdown(f'<div class="data-status">המגמות החמות ביותר בגוגל ישראל | עדכון אחרון: {update_time}</div>', unsafe_allow_html=True)

    for i, trend in enumerate(trends_list):
        search_query = trend['title']
        news = get_news(search_query)
        google_search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        
        # בניית רשימת החדשות ב-HTML נקי
        news_html = ""
        for n in news:
            news_html += f"""
            <div class='news-item'>
                <span class='source-tag'>{n['source']}</span>
                <span class='date-tag'>{n['date']}</span>
                <a href='{n['link']}' target='_blank' class='news-link'>{n['title']}</a>
            </div>
            """
        
        if not news_html:
            news_html = "<p style='color:#999;'>לא נמצאו ידיעות רלוונטיות כרגע.</p>"

        # רינדור הכרטיס (הכל ב-Markdown אחד כדי למנוע "שבירה" של ה-HTML)
        st.markdown(f"""
        <div class='trend-card'>
            <div style='color:#4285F4; font-weight:800; font-size: 0.9rem; margin-bottom:5px;'>#{i+1} במגמות החיפוש</div>
            <a href='{google_search_url}' target='_blank' class='item-title-link'>{search_query}</a>
            <div style='margin-top:10px;'><span class='traffic-badge'>🔥 {trend['traffic']} חיפושים</span></div>
            <div class='news-box'>
                <div style='font-weight:800; color:#444; margin-bottom:15px; font-size:1.1rem;'>למה כולם מחפשים את זה?</div>
                {news_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("לא ניתן לטעון את המגמות. נסה לרענן.")
