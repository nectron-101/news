import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse
import time

st.set_page_config(page_title="WikiNews Pro Israel", layout="wide", page_icon="🇮🇱")

# CSS חזק ל-RTL ועיצוב נקי
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"] {
        direction: rtl !important; text-align: right !important; font-family: 'Assistant', sans-serif !important;
    }
    .main-title { color: #ee3124; font-size: 3rem; font-weight: 800; text-align: center !important; margin-bottom: 20px; border-bottom: 4px solid #ee3124; }
    .news-card { background: white; border-right: 8px solid #ee3124; padding: 20px; margin-bottom: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .wiki-img { width: 100%; max-height: 300px; object-fit: cover; border-radius: 4px; margin-bottom: 15px; }
    .source-tag { background: #ee3124; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8rem; margin-left: 10px; font-weight: bold; }
    .news-item { margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    a { text-decoration: none !important; color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_top_articles():
    # ניסיון להביא אתמול, אם לא קיים - שלשום
    for days_back in [1, 2]:
        target_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{target_date}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNewsIsrael/2.1'}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                articles = data['items'][0]['articles']
                exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
                return [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
        except: continue
    return []

def get_wiki_meta(title):
    try:
        url = f"https://he.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages|info&format=json&pithumbsize=500&inprop=url"
        data = requests.get(url, timeout=5).json()
        page = list(data['query']['pages'].values())[0]
        return {
            "image": page.get('thumbnail', {}).get('source', ""),
            "read_time": max(1, round(page.get('length', 0) / 1500))
        }
    except: return {"image": "", "read_time": 1}

def get_google_news(query):
    encoded = urllib.parse.quote(query.replace('_', ' '))
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        news = []
        for item in root.findall('.//item')[:3]:
            t = item.find('title').text
            news.append({
                "title": t.split(" - ")[0] if " - " in t else t,
                "source": item.find('source').text if item.find('source') is not None else "חדשות",
                "link": item.find('link').text
            })
        return news
    except: return []

# --- בניית הממשק ---
st.markdown('<div class="main-title">WIKI-NEWS ISRAEL</div>', unsafe_allow_html=True)

with st.status("אוסף נתונים מוויקיפדיה...", expanded=True) as status:
    top_list = fetch_top_articles()
    if not top_list:
        st.error("לא הצלחתי להתחבר לשרתי ויקיפדיה. נסה לרענן בעוד כמה דקות.")
        st.stop()
    status.update(label="הנתונים הגיעו! מעבד תוכן...", state="complete")

for i, art in enumerate(top_list):
    title_clean = art['article'].replace('_', ' ')
    
    with st.container():
        # יצירת כרטיס
        col1, col2 = st.columns([1, 2])
        
        # שליפת מטא וחדשות לכל אייטם בנפרד כדי למנוע קריסה
        meta = get_wiki_meta(art['article'])
        news = get_google_news(title_clean)
        
        with st.expander(f"מקום {i+1}: {title_clean} ({art['views']:,} צפיות)", expanded=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                if meta['image']:
                    st.image(meta['image'], use_column_width=True)
                st.write(f"⏱️ כ-{meta['read_time']} דק' קריאה")
                st.markdown(f"[🔗 לערך המלא בוויקיפדיה](https://he.wikipedia.org/wiki/{art['article']})")
            
            with c2:
                st.write("**למה זה בחדשות?**")
                if news:
                    for n in news:
                        st.markdown(f"""<div class="news-item">
                            <span class="source-tag">{n['source']}</span>
                            <a href="{n['link']}" target="_blank">{n['title']}</a>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.write("לא נמצאו ידיעות ישירות כרגע.")
