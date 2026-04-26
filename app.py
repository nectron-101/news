import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Pro Israel", layout="wide", page_icon="🇮🇱")

# CSS מתקדם - RTL, עיצוב כרטיסים משופר ותמיכה בתמונות
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], [data-testid="stMarkdownContainer"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center !important;
        margin-bottom: 5px;
    }

    .sub-header {
        text-align: center !important;
        margin-bottom: 40px;
        color: #555;
        font-size: 1.2rem;
    }

    .news-card {
        background-color: white;
        border-right: 10px solid #ee3124;
        padding: 0;
        margin-bottom: 35px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .card-content { padding: 25px; }

    .wiki-image {
        width: 100%;
        height: 250px;
        object-fit: cover;
        border-bottom: 1px solid #eee;
    }

    .source-favicon {
        width: 16px;
        height: 16px;
        margin-left: 8px;
        vertical-align: middle;
    }

    .news-item {
        background: #fdfdfd;
        margin-bottom: 10px;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #f0f0f0;
        display: flex;
        align-items: center;
    }

    .meta-info {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 10px;
        display: flex;
        gap: 15px;
    }

    .reading-time { color: #28a745; font-weight: bold; }

    a { text-decoration: none !important; color: inherit; }
    h2 a { color: #0056b3 !important; }
    h2 a:hover { color: #ee3124 !important; }
    </style>
    """, unsafe_allow_html=True)

# כפתור רענון בסרגל הצד
if st.sidebar.button("🔄 רענון נתונים"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def get_wiki_data():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    top_url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    
    try:
        r = requests.get(top_url, headers={'User-Agent': 'WikiNewsPro/2.0'}, timeout=10)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
        top_20 = [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
        
        # העשרת נתונים (תמונות וזמן קריאה)
        enriched = []
        for art in top_20:
            title = art['article']
            meta_url = f"https://he.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages|info&format=json&pithumbsize=600&inprop=url"
            meta_r = requests.get(meta_url).json()
            page_id = list(meta_r['query']['pages'].keys())[0]
            page_data = meta_r['query']['pages'][page_id]
            
            img_url = page_data.get('thumbnail', {}).get('source', "")
            length = page_data.get('length', 0)
            read_time = max(1, round(length / 1500)) # הערכה גסה: 1500 תווים לדקה
            
            enriched.append({
                'title': title.replace('_', ' '),
                'raw_title': title,
                'views': art['views'],
                'image': img_url,
                'read_time': read_time
            })
        return enriched
    except: return []

def get_news(query):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:5]:
            full_title = item.find('title').text
            link = item.find('link').text
            domain = urllib.parse.urlparse(link).netloc
            favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
            
            title = full_title.split(" - ")[0] if " - " in full_title else full_title
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            
            pub_date = item.find('pubDate').text
            try:
                dt = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                date_str = dt.strftime('%d/%m')
            except: date_str = ""

            items.append({"title": title, "link": link, "source": source, "date": date_str, "favicon": favicon})
        return items
    except: return []

# תצוגה
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">האייטמים הכי נצפים אתמול והקשרם החדשותי</div>', unsafe_allow_html=True)

data = get_wiki_data()

if not data:
    st.warning("מתחבר למקורות הנתונים... נסה לרענן.")
else:
    for i, item in enumerate(data):
        news_list = get_news(item['title'])
        
        # בניית רשימת חדשות עם פאביקונים
        news_html = ""
        for n in news_list:
            news_html += f"""
            <div class="news-item">
                <img src="{n['favicon']}" class="source-favicon">
                <span style="font-size:0.8rem; color:#ee3124; font-weight:bold; margin-left:10px;">{n['source']}</span>
                <span style="font-size:0.8rem; color:#888; margin-left:10px;">{n['date']}</span>
                <a href="{n['link']}" target="_blank" style="font-weight:500;">{n['title']}</a>
            </div>
            """
        
        if not news_html:
            news_html = "<p style='color:#999;'>לא נמצאו ידיעות ישירות מהיממה האחרונה.</p>"

        # תמונה (אם קיימת)
        image_tag = f'<img src="{item["image"]}" class="wiki-image">' if item['image'] else '<div style="height:20px;"></div>'

        # כרטיס סופי
        card = f"""
        <div class="news-card">
            {image_tag}
            <div class="card-content">
                <div class="meta-info">
                    <span>מקום {i+1} בפופולריות</span>
                    <span>👁️ {item['views']:,} צפיות</span>
                    <span class="reading-time">⏱️ {item['read_time']} דק' קריאה</span>
                </div>
                <h2 style="margin: 0 0 15px 0;"><a href="https://he.wikipedia.org/wiki/{item['raw_title']}" target="_blank">{item['title']}</a></h2>
                <div style="font-weight: bold; margin-bottom: 15px; border-top: 1px solid #eee; padding-top: 15px; color: #444;">למה זה בחדשות?</div>
                {news_html}
            </div>
        </div>
        """
        st.markdown(card, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.write("מערכת WikiNews Pro מושכת נתונים מ-Wikimedia API ו-Google News RSS.")
