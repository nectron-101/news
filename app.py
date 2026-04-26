import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Israel", layout="wide", page_icon="🗞️")

# CSS - יישור לימין (RTL) ועיצוב כרטיסי חדשות
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    /* יישור גלובלי לימין */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
        background-color: #f8f9fa;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center !important;
        border-bottom: 5px solid #ee3124;
        padding-bottom: 10px;
        margin-bottom: 40px;
    }

    /* עיצוב כרטיס אייטם פתוח */
    .item-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 35px;
        padding: 25px;
        border-right: 12px solid #ee3124;
        direction: rtl;
    }

    .rank-label {
        color: #ee3124;
        font-weight: bold;
        font-size: 1rem;
        margin-bottom: 5px;
    }

    .item-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 5px;
        display: block;
    }
    
    .item-title a {
        color: #0056b3;
        text-decoration: none;
    }

    .item-title a:hover {
        color: #ee3124;
    }

    .views-label {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }

    .news-container {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #eee;
    }

    .news-row {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        padding: 8px;
        background: #fdfdfd;
        border-radius: 5px;
        border: 1px solid #f1f1f1;
    }

    .source-tag {
        background: #ee3124;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 15px;
        white-space: nowrap;
    }

    .date-tag {
        color: #999;
        font-size: 0.85rem;
        margin-left: 15px;
        white-space: nowrap;
    }

    .news-link {
        color: #333;
        font-weight: 500;
        text-decoration: none;
        font-size: 1.1rem;
    }

    .news-link:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top():
    # בדיקת אתמול, ואם לא קיים - שלשום
    for i in [1, 2]:
        date_str = (datetime.now() - timedelta(days=i)).strftime('%Y/%m/%d')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{date_str}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNewsIsrael/4.0'}, timeout=10)
            if r.status_code == 200:
                articles = r.json()['items'][0]['articles']
                exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
                return [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
        except: continue
    return []

def get_news(query):
    encoded = urllib.parse.quote(query.replace('_', ' '))
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        results = []
        # שליפת עד 6 מקורות כפי שביקשת
        for item in root.findall('.//item')[:6]:
            title = item.find('title').text.split(" - ")[0]
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            pub_date = item.find('pubDate').text
            try:
                date_formatted = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m')
            except: date_formatted = ""
            results.append({
                "title": title,
                "link": item.find('link').text,
                "source": source,
                "date": date_formatted
            })
        return results
    except: return []

# רינדור האתר
st.markdown('<div class="main-title">WIKI-NEWS ISRAEL</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; margin-bottom: 40px;">הנושאים הכי מחופשים בישראל והקשרם החדשותי</p>', unsafe_allow_html=True)

data = get_wiki_top()

if not data:
    st.error("לא ניתן לשלוף נתונים כרגע. נסה לרענן בעוד דקה.")
else:
    for i, art in enumerate(data):
        title_clean = art['article'].replace('_', ' ')
        news_items = get_news(title_clean)
        
        # בניית רשימת החדשות
        news_rows_html = ""
        for n in news_items:
            news_rows_html += f"""
            <div class="news-row">
                <span class="source-tag">{n['source']}</span>
                <span class="date-tag">{n['date']}</span>
                <a class="news-link" href="{n['link']}" target="_blank">{n['title']}</a>
            </div>
            """
        
        if not news_rows_html:
            news_rows_html = "<p style='color:#999;'>לא נמצאו ידיעות חדשותיות רלוונטיות מהיממה האחרונה.</p>"

        # הצגת כרטיס אייטם פתוח
        card_html = f"""
        <div class="item-card">
            <div class="rank-label">מקום {i+1} במדד הפופולריות</div>
            <div class="item-title">
                <a href="https://he.wikipedia.org/wiki/{art['article']}" target="_blank">{title_clean}</a>
            </div>
            <div class="views-label">👁️ {art['views']:,} צפיות אתמול</div>
            
            <div class="news-container">
                <p style="font-weight: bold; color: #444; margin-bottom: 15px;">למה זה בחדשות?</p>
                {news_rows_html}
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<br><center style='color: #bbb; font-size: 0.8rem;'>נתונים מוויקיפדיה וחדשות גוגל</center>", unsafe_allow_html=True)
