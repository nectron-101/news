import streamlit as st
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="Google Trends Israel", layout="wide", page_icon="🔥")

# CSS מתקדם - RTL, עיצוב יוקרתי וסינכרון שורות מושלם
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], .stMarkdown {
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
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 40px;
        padding-top: 10px;
        border-top: 1px solid #eee;
        width: 50%;
        margin-left: auto;
        margin-right: auto;
    }

    .trend-card {
        background-color: #ffffff;
        border-right: 8px solid #4285F4;
        padding: 35px;
        margin-bottom: 30px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    
    .trend-card:hover {
        transform: scale(1.005);
    }

    .item-link {
        color: #1a1a1a !important;
        font-size: 2.5rem;
        font-weight: 800;
        text-decoration: none !important;
        display: block;
        margin-bottom: 8px;
    }
    
    .item-link:hover {
        color: #4285F4 !important;
    }

    .traffic-info {
        background: #e8f0fe;
        color: #1967d2;
        padding: 4px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 25px;
    }

    .section-label {
        font-weight: 800;
        color: #1a1a1a;
        font-size: 1rem;
        margin-bottom: 20px;
        display: block;
        border-bottom: 2px solid #f8f9fa;
        padding-bottom: 5px;
    }

    /* סינכרון שורת החדשות */
    .news-item {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px;
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #f1f1f1;
        margin-bottom: 12px;
        transition: background 0.2s;
    }

    .news-item:hover {
        background-color: #f8fbff;
    }

    .source-tag {
        background-color: #4285F4;
        color: white;
        padding: 4px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: 800;
        min-width: 70px;
        text-align: center;
    }

    .date-tag {
        color: #999;
        font-size: 0.85rem;
        min-width: 45px;
        text-align: center;
    }

    .news-link {
        color: #333 !important;
        font-weight: 600;
        text-decoration: none !important;
        font-size: 1.1rem;
        flex-grow: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .news-link:hover {
        color: #4285F4 !important;
        text-decoration: underline !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def fetch_google_trends():
    url = "https://trends.google.com/trending/rss?geo=IL"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        # Namespace for Google Trends RSS
        ns = {'ht': 'http://namespaces.google.com/trends/hottrends'}
        
        trends = []
        for item in root.findall('.//item'):
            title = item.find('title').text
            traffic = item.find('ht:approx_traffic', ns).text if item.find('ht:approx_traffic', ns) is not None else ""
            trends.append({"title": title, "traffic": traffic})
        return trends[:20]
    except Exception as e:
        return []

def get_google_news(query):
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
                "title": full_title.split(" - ")[0] if " - " in full_title else full_title,
                "source": item.find('source').text if item.find('source') is not None else "חדשות",
                "link": item.find('link').text,
                "date": date_str
            })
        return news
    except: return []

# --- תצוגה ---
st.markdown('<h1 class="main-title">GOOGLE TRENDS ISRAEL</h1>', unsafe_allow_html=True)

trends_list = fetch_google_trends()

if trends_list:
    update_time = datetime.now().strftime('%H:%M')
    st.markdown(f'<div class="data-status">המגמות החמות ביותר בגוגל ישראל | עדכון אחרון: {update_time}</div>', unsafe_allow_html=True)

    for i, trend in enumerate(trends_list):
        search_query = trend['title']
        news = get_google_news(search_query)
        
        # בניית הכרטיס
        st.markdown(f"""
        <div class="trend-card">
            <div style="color:#4285F4; font-weight:800; font-size: 0.9rem; margin-bottom:5px;">#{i+1} במגמות החיפוש</div>
            <a href="https://www.google.com/search?q={urllib.parse.quote(search_query)}" target="_blank" class="item-link">{search_query}</a>
            <div class="traffic-info">🔥 {trend['traffic']} חיפושים</div>
            
            <span class="section-label">למה כולם מחפשים את זה?</span>
        """, unsafe_allow_html=True)
        
        if news:
            for n in news:
                st.markdown(f"""
                <div class="news-item">
                    <span class="source-tag">{n['source']}</span>
                    <span class="date-tag">{n['date']}</span>
                    <a href="{n['link']}" target="_blank" class="news-link">{n['title']}</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("לא נמצאו ידיעות רלוונטיות כרגע.")
        
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.error("לא ניתן לטעון את המגמות כרגע. נסה לרענן בעוד דקה.")
