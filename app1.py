import streamlit as st
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="Google Trends Israel", layout="wide", page_icon="🔥")

# CSS "סקסי" ויוקרתי - RTL מלא, כותרות לחיצות ועיצוב נקי
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
    
    /* יישור גלובלי אגרסיבי */
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
        border-radius: 12px;
        margin-bottom: 30px;
        font-weight: bold;
        color: #555;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
        border: 1px solid #eee;
    }

    .trend-card {
        background-color: #ffffff;
        border-right: 12px solid #4285F4;
        padding: 30px;
        margin-bottom: 35px;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
    }

    .trend-card:hover {
        transform: translateY(-5px);
    }
    
    .item-title-link {
        color: #1a1a1a !important;
        font-size: 2.8rem;
        font-weight: 800;
        text-decoration: none !important;
        transition: color 0.2s;
        line-height: 1.2;
    }
    
    .item-title-link:hover {
        color: #4285F4 !important;
    }

    .traffic-badge {
        background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
        color: #1967d2;
        padding: 6px 18px;
        border-radius: 25px;
        font-size: 0.95rem;
        font-weight: 700;
        display: inline-block;
        margin-top: 15px;
        margin-bottom: 25px;
        border: 1px solid #c6dafc;
    }

    .news-box {
        margin-top: 10px;
        border-top: 2px solid #f8f9fa;
        padding-top: 20px;
    }

    .news-item {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 15px;
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid #f1f1f1;
        margin-bottom: 12px;
        transition: all 0.2s;
    }

    .news-item:hover {
        background-color: #f8fbff;
        border-color: #d2e3fc;
        transform: scale(1.01);
    }

    .source-tag {
        background-color: #4285F4;
        color: white;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 800;
        min-width: 85px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(66, 133, 244, 0.2);
    }

    .date-tag {
        color: #999;
        font-size: 0.85rem;
        min-width: 55px;
        font-weight: 400;
    }

    .news-link {
        color: #333 !important;
        font-weight: 600;
        text-decoration: none !important;
        font-size: 1.15rem;
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
    headers = {'User-Agent': 'Mozilla/5.0'}
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
        
        # בניית רשימת החדשות ב-HTML נקי ללא הזחות
        news_html = ""
        for n in news:
            news_html += f"<div class='news-item'><span class='source-tag'>{n['source']}</span><span class='date-tag'>{n['date']}</span><a href='{n['link']}' target='_blank' class='news-link'>{n['title']}</a></div>"
        
        if not news_html:
            news_html = "<p style='color:#999;'>לא נמצאו ידיעות רלוונטיות כרגע.</p>"

        # רינדור הכרטיס - חשוב: המחרוזת צריכה להתחיל ללא רווחים בתחילת שורה
        card_content = f"""
<div class='trend-card'>
<div style='color:#4285F4; font-weight:800; font-size: 0.95rem; margin-bottom:8px;'>#{i+1} במגמות החיפוש</div>
<a href='{google_search_url}' target='_blank' class='item-title-link'>{search_query}</a>
<div><span class='traffic-badge'>🔥 {trend['traffic']} חיפושים</span></div>
<div class='news-box'>
<div style='font-weight:800; color:#1a1a1a; margin-bottom:18px; font-size:1.2rem;'>למה כולם מחפשים את זה?</div>
{news_html}
</div>
</div>
"""
        st.markdown(card_content, unsafe_allow_html=True)
else:
    st.error("לא ניתן לטעון את המגמות. נסה לרענן.")
