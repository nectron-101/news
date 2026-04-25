import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ועיצוב CSS קשיח ל-RTL
st.set_page_config(page_title="WikiNews Israel", layout="wide")

# הזרקת CSS שקובע יישור לימין לכל האפליקציה בצורה אגרסיבית
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    /* הגדרת כיוון גלובלית */
    html, body, [data-testid="stAppViewContainer"], .main {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        border-bottom: 4px solid #ee3124;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }

    .news-card {
        background-color: #ffffff;
        border-right: 8px solid #ee3124;
        padding: 20px;
        margin-bottom: 25px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        direction: rtl;
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
        display: inline-block;
    }

    .news-item {
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 1px solid #f0f0f0;
    }

    a {
        text-decoration: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציות שליפת נתונים
@st.cache_data(ttl=3600)
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNewsApp/1.1'}, timeout=10)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
        # שליפת 20 ערכים
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
    except:
        return []

def get_news(query):
    clean_query = query.replace('_', ' ')
    encoded = urllib.parse.quote(clean_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        items = []
        # שליפת עד 5 מקורות
        for item in root.findall('.//item')[:5]:
            full_title = item.find('title').text
            title = full_title.split(" - ")[0] if " - " in full_title else full_title
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            items.append({
                "title": title,
                "link": item.find('link').text,
                "source": source
            })
        return items
    except:
        return []

# 3. תצוגת האתר
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">הנושאים הכי חמים בישראל אתמול והקשרם החדשותי</p>', unsafe_allow_html=True)

data = get_wiki_top_views()

if not data:
    st.error("לא ניתן לטעון נתונים כרגע.")
else:
    for i, item in enumerate(data):
        article_name = item['article'].replace('_', ' ')
        news_list = get_news(article_name)
        
        # בניית ה-HTML של הכתבות
        news_html = ""
        if news_list:
            for n in news_list:
                news_html += f"""
                <div class="news-item">
                    <span class="source-tag">{n['source']}</span>
                    <a href="{n['link']}" target="_blank" style="color: #333;">{n['title']}</a>
                </div>
                """
        else:
            news_html = "<p style='color: #999;'>לא נמצאו ידיעות חדשותיות ישירות.</p>"

        # הצגת כרטיס הערך
        st.markdown(f"""
        <div class="news-card">
            <div style="font-size: 0.8rem; color: #666;">מקום {i+1} במדד הפופולריות</div>
            <h2 style="margin: 5px 0;"><a href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank" style="color: #0056b3;">{article_name}</a></h2>
            <div style="font-size: 0.8rem; color: #999; margin-bottom: 15px;">{item['views']:,} צפיות אתמול</div>
            <div style="font-weight: bold; margin-bottom: 10px; border-top: 1px solid #eee; padding-top: 10px;">למה זה בחדשות?</div>
            {news_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr><center style='color: #999; font-size: 0.8rem;'>מקורות: Wikimedia API & Google News RSS</center>", unsafe_allow_html=True)
