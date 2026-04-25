import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף ועיצוב CSS בסיסי
st.set_page_config(page_title="WikiNews Israel", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
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

    /* עיצוב כרטיס הידיעה */
    .news-container {
        background-color: #ffffff;
        border-right: 6px solid #ee3124;
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 2px 7px;
        border-radius: 3px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-left: 10px;
    }

    a {
        text-decoration: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. פונקציות שליפת נתונים
@st.cache_data(ttl=3600) # שמירת נתונים לשעה כדי להאיץ את האתר
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNewsIsrael/1.0'}, timeout=10)
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:"]
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:10]
    except Exception as e:
        return []

def get_news(query):
    clean_query = query.replace('_', ' ')
    encoded = urllib.parse.quote(clean_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:2]:
            full_title = item.find('title').text
            # ניקוי הכותרת - הסרת שם האתר בסוף
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

# 3. בניית הממשק
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.write("<center>הנושאים הכי מחופשים אתמול והקשרם החדשותי</center>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner('אוסף נתונים מוויקיפדיה וחדשות גוגל...'):
    data = get_wiki_top_views()

if not data:
    st.error("לא הצלחנו לשלוף נתונים. נסה לרענן את הדף.")
else:
    for i, item in enumerate(data):
        article_name = item['article'].replace('_', ' ')
        views = item['views']
        news_list = get_news(article_name)
        
        # יצירת "כרטיס" לכל אייטם
        with st.container():
            # שימוש ב-HTML פשוט מאוד בתוך ה-Markdown כדי למנוע שגיאות תצוגה
            st.markdown(f"""
            <div class="news-container">
                <div style="font-size: 0.9rem; color: #666;">מקום {i+1} במדד הפופולריות</div>
                <h2 style="margin-top: 0;"><a href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank" style="color: #0056b3;">{article_name}</a></h2>
                <div style="font-size: 0.85rem; color: #888; margin-bottom: 15px;">👁️ {views:,} צפיות אתמול</div>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p><strong>למה זה בחדשות?</strong></p>
            """, unsafe_allow_html=True)
            
            if news_list:
                for n in news_list:
                    # הזרקת החדשות בצורה בטוחה
                    st.markdown(f"""
                    <div style="margin-bottom: 10px; padding-right: 10px;">
                        <span class="source-tag">{n['source']}</span>
                        <a href="{n['link']}" target="_blank" style="color: #222; font-size: 1.1rem;">{n['title']}</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("לא נמצאו ידיעות חדשותיות רלוונטיות מהיממה האחרונה.")
                
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")
st.caption("הנתונים מבוססים על Wikimedia API ו-Google News RSS")
