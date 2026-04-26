import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Israel", layout="wide", page_icon="🗞️")

# CSS - עיצוב אתר חדשות פתוח ומיושר לימין
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
        background-color: #f4f7f9;
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

    /* כרטיס אייטם פתוח */
    .item-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        margin-bottom: 40px;
        overflow: hidden;
        border-right: 12px solid #ee3124;
        display: flex;
        flex-direction: row;
        min-height: 350px;
    }

    .item-image-container {
        flex: 1;
        min-width: 300px;
        background-color: #eee;
    }

    .item-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .item-content {
        flex: 2;
        padding: 30px;
        display: flex;
        flex-direction: column;
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
        margin-bottom: 10px;
        color: #222;
        text-decoration: none;
    }

    .item-title:hover { color: #ee3124; }

    .news-section {
        margin-top: 20px;
        border-top: 1px solid #eee;
        padding-top: 20px;
    }

    .news-entry {
        margin-bottom: 15px;
        padding: 10px;
        background: #f9f9f9;
        border-radius: 6px;
        display: flex;
        align-items: center;
    }

    .news-source {
        background: #ee3124;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
        margin-left: 15px;
        white-space: nowrap;
    }

    .news-date {
        color: #888;
        font-size: 0.85rem;
        margin-left: 15px;
    }

    .news-link {
        color: #333;
        font-weight: 500;
        text-decoration: none;
        font-size: 1.1rem;
    }

    /* התאמה לנייד */
    @media (max-width: 768px) {
        .item-card { flex-direction: column; }
        .item-image-container { height: 200px; min-width: 100%; }
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNewsIsrael/3.0'}, timeout=10)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
    except: return []

def get_wiki_image(title):
    # שליפה ישירה של תמונת הערך מה-API הרשמי
    encoded_title = urllib.parse.quote(title)
    url = f"https://he.wikipedia.org/w/api.php?action=query&titles={encoded_title}&prop=pageimages&format=json&pithumbsize=600"
    try:
        data = requests.get(url, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        page_id = list(pages.keys())[0]
        return pages[page_id].get('thumbnail', {}).get('source', "")
    except: return ""

def get_news_list(query):
    encoded = urllib.parse.quote(query.replace('_', ' '))
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        results = []
        for item in root.findall('.//item')[:5]:
            title = item.find('title').text.split(" - ")[0]
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            pub_date = item.find('pubDate').text
            try:
                date_str = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m')
            except: date_str = ""
            results.append({"title": title, "link": item.find('link').text, "source": source, "date": date_str})
        return results
    except: return []

# רינדור האתר
st.markdown('<div class="main-title">WIKI-NEWS ISRAEL</div>', unsafe_allow_html=True)

data = get_wiki_top()

if not data:
    st.error("לא ניתן לשלוף נתונים. נסה שנית.")
else:
    for i, art in enumerate(data):
        title_clean = art['article'].replace('_', ' ')
        img_url = get_wiki_image(art['article'])
        news = get_news_list(title_clean)
        
        # בניית רכיב החדשות
        news_html = ""
        for n in news:
            news_html += f"""
            <div class="news-entry">
                <span class="news-source">{n['source']}</span>
                <span class="news-date">{n['date']}</span>
                <a class="news-link" href="{n['link']}" target="_blank">{n['title']}</a>
            </div>
            """
        
        if not news_html:
            news_html = "<p style='color:#999;'>לא נמצאו ידיעות רלוונטיות מהיממה האחרונה.</p>"

        # הצגת הכרטיס המלא (פתוח)
        img_tag = f'<img src="{img_url}" class="item-image">' if img_url else '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#ccc;">אין תמונה</div>'
        
        card_html = f"""
        <div class="item-card">
            <div class="item-image-container">
                {img_tag}
            </div>
            <div class="item-content">
                <div class="rank-label">מקום {i+1} במדד הפופולריות • {art['views']:,} צפיות</div>
                <a class="item-title" href="https://he.wikipedia.org/wiki/{art['article']}" target="_blank">{title_clean}</a>
                <div class="news-section">
                    <p style="font-weight:bold; margin-bottom:15px; color:#444;">למה זה בחדשות?</p>
                    {news_html}
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
