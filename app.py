import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ו-CSS חזק ליישור לימין
st.set_page_config(page_title="WikiNews Israel", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    /* כפיית RTL על כל רכיבי האתר */
    html, body, [data-testid="stAppViewContainer"], .main, .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        border-bottom: 4px solid #ee3124;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }

    .news-card {
        background-color: white;
        border-right: 8px solid #ee3124;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }

    .date-tag {
        color: #888;
        font-size: 0.75rem;
        margin-left: 10px;
    }

    .news-item {
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #f4f4f4;
    }

    a {
        text-decoration: none !important;
    }

    /* תיקון נקודות תפריט ורשימות שיהיו בימין */
    ul {
        list-style-position: inside;
        padding-right: 0;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNews/1.4'}, timeout=12)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
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
        for item in root.findall('.//item')[:5]:
            full_title = item.find('title').text
            title = full_title.split(" - ")[0] if " - " in full_title else full_title
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            
            # חילוץ תאריך
            raw_date = item.find('pubDate').text # Format: Sat, 25 Apr 2026 14:30:00 GMT
            try:
                date_obj = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %Z')
                formatted_date = date_obj.strftime('%d/%m')
            except:
                formatted_date = ""

            items.append({
                "title": title, 
                "link": item.find('link').text, 
                "source": source,
                "date": formatted_date
            })
        return items
    except:
        return []

# תצוגה
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center;">הנושאים הכי חמים בישראל אתמול והקשרם החדשותי</p>', unsafe_allow_html=True)

data = get_wiki_top_views()

if not data:
    st.error("לא ניתן לטעון נתונים. נסה שנית מאוחר יותר.")
else:
    for i, item in enumerate(data):
        name = item['article'].replace('_', ' ')
        news_list = get_news(name)
        
        # בניית רשימת החדשות
        news_html = ""
        for n in news_list:
            date_str = f'<span class="date-tag">{n["date"]}</span>' if n["date"] else ""
            news_html += f"""
            <div class="news-item">
                <span class="source-tag">{n['source']}</span>
                {date_str}
                <a href="{n['link']}" target="_blank" style="color: #222; font-weight: 500;">{n['title']}</a>
            </div>
            """
        
        if not news_html:
            news_html = "<p style='color: #999;'>לא נמצאו ידיעות רלוונטיות מהיממה האחרונה.</p>"

        # הצגת כרטיס הערך
        st.markdown(f"""
        <div class="news-card">
            <div style="font-size: 0.8rem; color: #666;">מקום {i+1} במדד הפופולריות</div>
            <h2 style="margin: 5px 0;"><a href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank" style="color: #0056b3;">{name}</a></h2>
            <div style="font-size: 0.8rem; color: #999; margin-bottom: 15px;">{item['views']:,} צפיות אתמול</div>
            <div style="font-weight: bold; margin-bottom: 12px; border-top: 1px dotted #ccc; padding-top: 12px;">למה זה בחדשות?</div>
            {news_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><center style='color: #999; font-size: 0.8rem;'>מקורות: Wikimedia API & Google News RSS</center>", unsafe_allow_html=True)
