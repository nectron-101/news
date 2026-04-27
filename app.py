import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Pro Israel", layout="wide", page_icon="🇮🇱")

# CSS חזק ליישור ימין (RTL), עיצוב כרטיסים ופס מגמות
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

    /* עיצוב פס מגמות גוגל */
    .trends-bar {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-right: 10px solid #4285F4;
        padding: 15px;
        margin-bottom: 30px;
        border-radius: 8px;
    }

    .trend-tag {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1967d2;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px;
        font-weight: bold;
        font-size: 0.95rem;
    }

    .wiki-card {
        background-color: #ffffff;
        border-right: 10px solid #ee3124;
        padding: 25px;
        margin-bottom: 40px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .news-item {
        margin-bottom: 12px;
        padding: 10px;
        background-color: #f9f9f9;
        border-radius: 5px;
        border-right: 4px solid #ee3124;
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
    }

    .item-title {
        color: #0056b3;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-decoration: none;
    }

    .views-info {
        color: #666;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1800) # ריענון מגמות כל חצי שעה
def get_google_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IL"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        trends = []
        for item in root.findall('.//item')[:6]:
            trends.append(item.find('title').text)
        return trends
    except:
        return []

@st.cache_data(ttl=3600)
def fetch_top_articles():
    update_time = datetime.now().strftime('%H:%M')
    for days_back in [1, 2]:
        dt = datetime.now() - timedelta(days=days_back)
        date_str = dt.strftime('%Y/%m/%d')
        display_date = dt.strftime('%d/%m/%Y')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{date_str}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNews/2.2'}, timeout=10)
            if r.status_code == 200:
                articles = r.json()['items'][0]['articles']
                exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
                filtered = [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
                return filtered, display_date, update_time
        except: continue
    return [], None, update_time

def get_wiki_meta(title):
    encoded_title = urllib.parse.quote(title)
    url = f"https://he.wikipedia.org/w/api.php?action=query&titles={encoded_title}&prop=pageimages|info&format=json&pithumbsize=600"
    try:
        data = requests.get(url, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        page = list(pages.values())[0]
        img_url = page.get('thumbnail', {}).get('source', "")
        return {"image": img_url, "read_time": max(1, round(page.get('length', 0) / 1500))}
    except: return {"image": "", "read_time": 1}

def get_google_news(query):
    encoded = urllib.parse.quote(query.replace('_', ' '))
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        news = []
        for item in root.findall('.//item')[:4]:
            t = item.find('title').text
            pub_date = item.find('pubDate').text
            try:
                date_str = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%d/%m')
            except: date_str = ""
            news.append({
                "title": t.split(" - ")[0] if " - " in t else t,
                "source": item.find('source').text if item.find('source') is not None else "חדשות",
                "link": item.find('link').text,
                "date": date_str
            })
        return news
    except: return []
        
# --- תצוגה ---
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)

top_list, data_date, last_update = fetch_top_articles()
trends = get_google_trends()

# 1. הצגת מגמות גוגל בראש הדף
if trends:
    st.markdown('<div class="trends-bar"><strong>🔥 עכשיו בגוגל ישראל:</strong><br>', unsafe_allow_html=True)
    trend_html = "".join([f'<span class="trend-tag">{t}</span>' for t in trends])
    st.markdown(f'<div>{trend_html}</div></div>', unsafe_allow_html=True)

# 2. חיווי סטטוס
if data_date:
    st.markdown(f'<div class="data-status">נתוני ויקיפדיה מיום: {data_date} | עדכון אחרון: {last_update}</div>', unsafe_allow_html=True)

# 3. רשימת הכתבות
if not top_list:
    st.error("לא ניתן לטעון נתונים.")
else:
    for i, art in enumerate(top_list):
        title_clean = art['article'].replace('_', ' ')
        meta = get_wiki_meta(art['article'])
        news = get_google_news(title_clean)
        
        st.markdown(f'<div class="wiki-card">', unsafe_allow_html=True)
        col_img, col_text = st.columns([1, 2.5])
        
        with col_img:
            if meta['image']:
                st.image(meta['image'], use_container_width=True)
            else:
                st.info("אין תמונה בערך")
            st.write(f"⏱️ כ-{meta['read_time']} דק' קריאה")
            st.markdown(f"[🔗 לערך המלא](https://he.wikipedia.org/wiki/{art['article']})")
        
        with col_text:
            st.markdown(f'<div class="rank-label" style="color:#ee3124; font-weight:bold;">מקום {i+1} במדד הפופולריות</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="item-title">{title_clean}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="views-info">👁️ {art["views"]:,} צפיות</div>', unsafe_allow_html=True)
            
            st.write("**למה זה בחדשות?**")
            if news:
                for n in news:
                    st.markdown(f"""
                    <div class="news-item">
                        <span class="source-tag">{n['source']}</span>
                        <span class="date-tag">{n['date']}</span>
                        <a href="{n['link']}" target="_blank" style="color: #222; font-weight: 500; text-decoration:none;">{n['title']}</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("לא נמצאו ידיעות חדשותיות רלוונטיות כרגע.")
        st.markdown('</div>', unsafe_allow_html=True)
