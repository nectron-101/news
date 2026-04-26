import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ו-CSS
st.set_page_config(page_title="WikiNews Israel", layout="wide")

# CSS קשיח ליישור לימין ועיצוב כרטיסים
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
        margin-bottom: 30px;
    }

    .news-card {
        background-color: #ffffff;
        border-right: 12px solid #ee3124;
        padding: 25px;
        margin-bottom: 35px;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .item-header {
        margin-bottom: 15px;
    }

    .item-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0056b3;
        text-decoration: none;
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 10px;
        display: inline-block;
    }

    .date-tag {
        color: #888;
        font-size: 0.8rem;
        margin-left: 10px;
    }

    .news-row {
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f1f1;
        display: block;
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
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_wiki_top():
    # בדיקת אתמול, ואם לא קיים - שלשום
    for i in [1, 2]:
        date_str = (datetime.now() - timedelta(days=i)).strftime('%Y/%m/%d')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{date_str}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNews/4.0'}, timeout=10)
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
        for item in root.findall('.//item')[:6]:
            full_title = item.find('title').text
            title = full_title.split(" - ")[0] if " - " in full_title else full_title
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

# רינדור
st.markdown('<div class="main-title">WIKI-NEWS ISRAEL</div>', unsafe_allow_html=True)

data = get_wiki_top()

if not data:
    st.error("לא ניתן לשלוף נתונים כרגע.")
else:
    for i, art in enumerate(data):
        name = art['article'].replace('_', ' ')
        news_items = get_news(name)
        
        # בניית קוד החדשות בנפרד למניעת תקלות שרשור
        news_html_list = []
        for n in news_items:
            news_html_list.append(f"""
                <div class="news-row">
                    <span class="source-tag">{n['source']}</span>
                    <span class="date-tag">{n['date']}</span>
                    <a class="news-link" href="{n['link']}" target="_blank">{n['title']}</a>
                </div>
            """)
        
        all_news = "".join(news_html_list) if news_html_list else "לא נמצאו ידיעות רלוונטיות."

        # יצירת הכרטיס
        card_content = f"""
        <div class="news-card">
            <div class="item-header">
                <div style="color: #666; font-size: 0.8rem;">מקום {i+1} במדד הפופולריות</div>
                <h2 style="margin: 5px 0;">
                    <a href="https://he.wikipedia.org/wiki/{art['article']}" target="_blank" style="color: #0056b3; text-decoration: none;">{name}</a>
                </h2>
                <div style="color: #999; font-size: 0.8rem;">👁️ {art['views']:,} צפיות אתמול</div>
            </div>
            <div style="font-weight: bold; margin-bottom: 15px; border-top: 1px solid #eee; padding-top: 15px; color: #444;">למה זה בחדשות?</div>
            {all_news}
        </div>
        """
        st.markdown(card_content, unsafe_allow_html=True)
