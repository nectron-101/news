import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ועיצוב CSS חסין ל-RTL
st.set_page_config(page_title="WikiNews Israel", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    /* הגדרות כלליות ליישור ימין */
    html, body, [class*="css"], .stApp {
        font-family: 'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        border-bottom: 4px solid #ee3124;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }

    .news-card {
        background-color: #ffffff;
        border-right: 8px solid #ee3124;
        padding: 25px;
        margin-bottom: 30px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        direction: rtl;
    }
    
    .wiki-rank-tag {
        font-size: 0.9rem;
        color: #666;
        font-weight: bold;
    }

    .wiki-header {
        color: #0056b3;
        font-size: 2rem;
        text-decoration: none;
        margin-bottom: 5px;
        display: block;
    }

    .news-section {
        margin-top: 20px;
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
    }

    .news-item {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #eee;
    }

    .source-label {
        background-color: #ee3124;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 12px;
        white-space: nowrap;
    }

    .news-text {
        color: #222;
        text-decoration: none;
        font-size: 1.05rem;
        line-height: 1.4;
    }

    .news-text:hover {
        color: #ee3124;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציות שליפת נתונים
@st.cache_data(ttl=3600)
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNewsApp/1.0'}, timeout=10)
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

# 3. תצוגה
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.write("<center>הנושאים הכי חמים בישראל אתמול והקשרם החדשותי</center>", unsafe_allow_html=True)

with st.spinner('מעדכן נתונים...'):
    data = get_wiki_top_views()

if not data:
    st.error("לא הצלחנו לשלוף נתונים. נסה שנית.")
else:
    for i, item in enumerate(data):
        article_name = item['article'].replace('_', ' ')
        views = item['views']
        news_list = get_news(article_name)
        
        # בניית הכרטיס המעוצב
        card_html = f"""
        <div class="news-card">
            <div class="wiki-rank-tag">מקום {i+1} במדד הפופולריות</div>
            <a class="wiki-header" href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank">{article_name}</a>
            <div style="color: #999; font-size: 0.85rem;">{views:,} צפיות אתמול</div>
            
            <div class="news-section">
                <p style="margin-top:0; font-weight: bold; color: #444;">חדשות אחרונות:</p>
        """
        
        if news_list:
            for n in news_list:
                card_html += f"""
                <div class="news-item">
                    <span class="source-label">{n['source']}</span>
                    <a class="news-text" href="{n['link']}" target="_blank">{n['title']}</a>
                </div>
                """
        else:
            card_html += "<p style='color:#999;'>לא נמצאו כתבות ישירות מהיממה האחרונה.</p>"
            
        card_html += "</div></div>"
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<br><center style='color:#ccc;'>הנתונים מבוססים על Wikimedia API ו-Google News</center>", unsafe_allow_html=True)
