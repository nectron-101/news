import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Israel", layout="wide")

# CSS - יישור לימין ועיצוב כרטיסים
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
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
        background-color: white;
        border-right: 8px solid #ee3124;
        padding: 20px;
        margin-bottom: 25px;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        direction: rtl;
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
        display: inline-block;
    }

    .news-item {
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #f0f0f0;
        line-height: 1.5;
    }

    a {
        text-decoration: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNews/1.5'}, timeout=10)
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
            
            # תאריך
            pub_date = item.find('pubDate').text
            try:
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                date_str = dt.strftime('%d/%m')
            except:
                date_str = ""

            items.append({"title": title, "link": item.find('link').text, "source": source, "date": date_str})
        return items
    except:
        return []

# כותרת
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.write("<center>הנושאים הכי חמים בישראל אתמול והקשרם החדשותי</center>", unsafe_allow_html=True)

data = get_wiki_top_views()

if not data:
    st.error("לא ניתן לטעון נתונים.")
else:
    for i, item in enumerate(data):
        name = item['article'].replace('_', ' ')
        news_list = get_news(name)
        
        # בניית רשימת החדשות - שימוש בגרש בודד למניעת התנגשויות
        news_rows = []
        for n in news_list:
            d_tag = f'<span class="date-tag">{n["date"]}</span>' if n["date"] else ""
            row = f'<div class="news-item"><span class="source-tag">{n["source"]}</span>{d_tag}<a href="{n["link"]}" target="_blank" style="color: #222;">{n["title"]}</a></div>'
            news_rows.append(row)
        
        all_news_html = "".join(news_rows) if news_rows else "לא נמצאו ידיעות רלוונטיות."

        # כרטיס סופי
        card = f"""
        <div class="news-card">
            <div style="font-size: 0.8rem; color: #666;">מקום {i+1}</div>
            <h2 style="margin: 5px 0;"><a href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank" style="color: #0056b3;">{name}</a></h2>
            <div style="font-size: 0.8rem; color: #999; margin-bottom: 15px;">{item['views']:,} צפיות אתמול</div>
            <div style="font-weight: bold; margin-bottom: 10px; border-top: 1px solid #eee; padding-top: 10px;">למה זה בחדשות?</div>
            <div>{all_news_html}</div>
        </div>
        """
        st.markdown(card, unsafe_allow_html=True)
