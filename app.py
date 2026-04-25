import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ועיצוב RTL
st.set_page_config(page_title="WikiNews Israel", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
    }

    .main-title {
        color: #ee3124;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        border-bottom: 3px solid #ee3124;
        padding-bottom: 15px;
        margin-bottom: 30px;
    }

    .news-card {
        background-color: white;
        border-right: 10px solid #ee3124;
        padding: 20px;
        margin-bottom: 25px;
        border-radius: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        direction: rtl;
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 10px;
        display: inline-block;
    }

    .news-item {
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f2f2f2;
        display: flex;
        align-items: center;
    }

    .news-link {
        color: #222;
        text-decoration: none;
        font-size: 1.1rem;
        font-weight: 500;
    }

    .news-link:hover {
        color: #ee3124;
    }

    .views-info {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNews/1.2'}, timeout=10)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
    except: return []

def get_news(query):
    clean_query = query.replace('_', ' ')
    encoded = urllib.parse.quote(clean_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        results = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text.split(" - ")[0]
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            results.append({"title": title, "link": item.find('link').text, "source": source})
        return results
    except: return []

# תצוגה
st.markdown('<div class="main-title">WIKI-NEWS ISRAEL</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #555;">הנושאים הכי מחופשים אתמול והקשרם החדשותי</p>', unsafe_allow_html=True)

data = get_wiki_top_views()

if not data:
    st.warning("טוען נתונים...")
else:
    for i, item in enumerate(data):
        name = item['article'].replace('_', ' ')
        news_list = get_news(name)
        
        # בנייה בטוחה של רשימת החדשות
        news_rows = ""
        for n in news_list:
            news_rows += f"""
            <div class="news-item">
                <span class="source-tag">{n['source']}</span>
                <a href="{n['link']}" class="news-link" target="_blank">{n['title']}</a>
            </div>
            """
        
        if not news_rows:
            news_rows = "<p style='color: #999;'>לא נמצאו כתבות ישירות מהיממה האחרונה.</p>"

        # הצגת הכרטיס המלא
        card_html = f"""
        <div class="news-card">
            <div style="font-size: 0.8rem; color: #666;">מקום {i+1} במדד הפופולריות</div>
            <h2 style="margin: 5px 0;"><a href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank" style="color: #0056b3; text-decoration: none;">{name}</a></h2>
            <div class="views-info">👁️ {item['views']:,} צפיות אתמול</div>
            <div style="font-weight: bold; margin-bottom: 15px; border-top: 1px solid #eee; padding-top: 10px; color: #444;">למה זה בחדשות?</div>
            {news_rows}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<br><center style='color: #999; font-size: 0.8rem;'>נתונים מוויקיפדיה וחדשות גוגל</center>", unsafe_allow_html=True)
