import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Pro Israel", layout="wide", page_icon="🇮🇱")

# CSS חזק - RTL ועיצוב כרטיסים (תיקון מבני למניעת "היעלמות" תוכן)
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
        margin-bottom: 5px;
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
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    .trend-tag {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1967d2;
        padding: 4px 10px;
        border-radius: 15px;
        margin: 4px;
        font-weight: bold;
        font-size: 0.9rem;
    }

    /* עיצוב הכרטיס */
    .wiki-card-wrap {
        border-right: 10px solid #ee3124;
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }

    .news-item {
        margin-bottom: 10px;
        padding: 8px;
        background-color: #f9f9f9;
        border-radius: 5px;
        border-right: 3px solid #ee3124;
    }

    .source-tag {
        background-color: #ee3124; color: white; padding: 2px 5px;
        border-radius: 3px; font-size: 0.75rem; font-weight: bold; margin-left: 8px;
    }

    .item-title { color: #0056b3; font-size: 1.8rem; font-weight: 700; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def get_google_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IL"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.31'}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.content)
        return [item.find('title').text for item in root.findall('.//item')[:7]]
    except: return []

@st.cache_data(ttl=3600)
def fetch_top_articles():
    update_time = datetime.now().strftime('%H:%M')
    for days_back in [1, 2]:
        dt = datetime.now() - timedelta(days=days_back)
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{dt.strftime('%Y/%m/%d')}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNews/3.0'}, timeout=10)
            if r.status_code == 200:
                filtered = [a for a in r.json()['items'][0]['articles'] if not any(x in a['article'] for x in ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:"])]
                return filtered[:20], dt.strftime('%d/%m/%Y'), update_time
        except: continue
    return [], None, update_time

def get_wiki_meta(title):
    try:
        url = f"https://he.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages|info&format=json&pithumbsize=500"
        page = list(requests.get(url, timeout=5).json()['query']['pages'].values())[0]
        return {"image": page.get('thumbnail', {}).get('source', ""), "time": max(1, round(page.get('length', 0) / 1500))}
    except: return {"image": "", "time": 1}

def get_google_news(query):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=he&gl=IL&ceid=IL:he"
    try:
        root = ET.fromstring(requests.get(url, timeout=5).content)
        return [{"title": i.find('title').text.split(" - ")[0], "source": i.find('source').text, "link": i.find('link').text, "date": i.find('pubDate').text[:11]} for i in root.findall('.//item')[:4]]
    except: return []

# --- תצוגה ---
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)

trends = get_google_trends()
if trends:
    trend_html = "".join([f'<span class="trend-tag">{t}</span>' for t in trends])
    st.markdown(f'<div class="trends-bar"><strong>🔥 עכשיו בגוגל ישראל:</strong><br>{trend_html}</div>', unsafe_allow_html=True)

top_list, data_date, last_update = fetch_top_articles()
if data_date:
    st.markdown(f'<div class="data-status">נתוני ויקיפדיה: {data_date} | עדכון אחרון: {last_update}</div>', unsafe_allow_html=True)

if not top_list:
    st.error("לא ניתן לטעון נתונים.")
else:
    for i, art in enumerate(top_list):
        title = art['article'].replace('_', ' ')
        meta = get_wiki_meta(art['article'])
        news = get_google_news(title)
        
        # שימוש ב-container של Streamlit במקום HTML חיצוני ששובר את התצוגה
        with st.container():
            st.markdown(f'<div class="wiki-card-wrap">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2.5])
            
            with col1:
                if meta['image']:
                    st.image(meta['image'], use_container_width=True)
                st.write(f"⏱️ כ-{meta['time']} דק' קריאה")
                st.markdown(f"[🔗 לערך המלא](https://he.wikipedia.org/wiki/{art['article']})")
            
            with col2:
                st.markdown(f'<div style="color:#ee3124; font-weight:bold;">מקום {i+1}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="item-title">{title}</div>', unsafe_allow_html=True)
                st.write(f"👁️ {art['views']:,} צפיות")
                st.write("---")
                if news:
                    for n in news:
                        st.markdown(f'<div class="news-item"><span class="source-tag">{n["source"]}</span><a href="{n["link"]}" target="_blank" style="color:#222; text-decoration:none;">{n["title"]}</a></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
