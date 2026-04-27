import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Pro Israel", layout="wide", page_icon="🇮🇱")

# CSS חזק ליישור ימין (RTL) ועיצוב נקי
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3rem;
        font-weight: 800;
        text-align: center !important;
        border-bottom: 4px solid #ee3124;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }

    .data-status {
        text-align: center !important;
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-weight: bold;
        color: #555;
        font-size: 0.85rem;
    }

    /* פס מגמות גוגל */
    .trends-bar {
        background-color: #ffffff;
        border-right: 10px solid #4285F4;
        padding: 15px;
        margin-bottom: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    .trend-tag {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1967d2;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 5px;
        font-weight: bold;
        font-size: 0.95rem;
    }

    .wiki-card {
        background-color: #ffffff;
        border-right: 12px solid #ee3124;
        padding: 25px;
        margin-bottom: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .news-item {
        margin-bottom: 12px;
        padding: 10px;
        background-color: #f9f9f9;
        border-radius: 5px;
        border-right: 4px solid #ee3124;
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 10px;
        display: inline-block;
    }

    .date-tag {
        color: #888;
        font-size: 0.75rem;
        margin-left: 10px;
    }

    .item-title {
        color: #0056b3;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 5px;
        display: block;
    }

    .views-info {
        color: #666;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def get_google_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IL"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        return [item.find('title').text for item in root.findall('.//item')[:8]]
    except:
        return []

@st.cache_data(ttl=3600)
def fetch_top_articles():
    update_time = datetime.now().strftime('%H:%M')
    for days_back in [1, 2]:
        dt = datetime.now() - timedelta(days=days_back)
        date_str = dt.strftime('%Y/%m/%d')
        display_date = dt.strftime('%d/%m/%Y')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{date_str}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNews/2.5'}, timeout=10)
            if r.status_code == 200:
                articles = r.json()['items'][0]['articles']
                exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
                filtered = [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
                return filtered, display_date, update_time
        except: continue
    return [], None, update_time

def get_google_news(query):
    encoded = urllib.parse.quote(query.replace('_', ' '))
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        news = []
        for item in root.findall('.//item')[:4]:
            t = item.find('title').text
            pub_date = item.find('pubDate').text
            try:
                date_str = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m')
            except: date_str = ""
            news.append({
                "title": t.split(" - ")[0] if " - " in t else t,
                "source": item.find('source').text if item.find('source') is not None else "חדשות",
                "link": item.find('link').text,
                "date": date_str
            })
        return news
    except: return []

# --- תצוגה ---
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)

# 1. מגמות גוגל טרנדס
trends = get_google_trends()
if trends:
    trend_html = "".join([f'<span class="trend-tag">{t}</span>' for t in trends])
    st.markdown(f'<div class="trends-bar"><strong>🔥 עכשיו בחיפושים (Google Trends):</strong><br>{trend_html}</div>', unsafe_allow_html=True)

# 2. חיווי נתונים
top_list, data_date, last_update = fetch_top_articles()
if data_date:
    st.markdown(f'<div class="data-status">נתוני ויקיפדיה מיום: {data_date} | עדכון אחרון: {last_update}</div>', unsafe_allow_html=True)

# 3. רשימת הכתבות
if not top_list:
    st.error("לא ניתן לטעון נתונים. נסה לרענן.")
else:
    for i, art in enumerate(top_list):
        title_clean = art['article'].replace('_', ' ')
        news = get_google_news(title_clean)
        
        # בניית רשימת החדשות לתוך מחרוזת
        news_html = ""
        for n in news:
            news_html += f"""
            <div class="news-item">
                <span class="source-tag">{n['source']}</span>
                <span class="date-tag">{n['date']}</span>
                <a href="{n['link']}" target="_blank" style="color: #222; font-weight: 500; text-decoration:none;">{n['title']}</a>
            </div>
            """
        
        if not news_html:
            news_html = "<p style='color:#999;'>לא נמצאו ידיעות חדשותיות רלוונטיות כרגע.</p>"

        # רינדור הכרטיס המלא
        st.markdown(f"""
        <div class="wiki-card">
            <div style="color:#ee3124; font-weight:bold; font-size: 0.9rem;">מקום {i+1} במדד הפופולריות</div>
            <div class="item-title"><a href="https://he.wikipedia.org/wiki/{art['article']}" target="_blank" style="color: #0056b3; text-decoration:none;">{title_clean}</a></div>
            <div class="views-info">👁️ {art["views"]:,} צפיות אתמול</div>
            <div style="font-weight: bold; margin-bottom: 15px; border-top: 1px solid #eee; padding-top: 15px; color: #444;">למה זה בחדשות?</div>
            {news_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><center style='color:#bbb;'>נתונים מוויקיפדיה וחדשות גוגל</center>", unsafe_allow_html=True)
