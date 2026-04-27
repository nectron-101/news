import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title="WikiNews Israel", layout="wide", page_icon="🗞️")

# CSS מתקדם למראה מודרני ויוקרתי
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stVerticalBlock"], .stMarkdown {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Assistant', sans-serif !important;
        background-color: #f8f9fa;
    }
    
    /* כותרת ראשית מעוצבת */
    .main-title {
        background: linear-gradient(90deg, #ee3124, #b3190f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center !important;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }

    .data-status {
        text-align: center !important;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 30px;
        padding: 5px;
        border-top: 1px solid #ddd;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }

    /* עיצוב כרטיס משודרג */
    .wiki-card {
        background-color: #ffffff;
        border-right: 6px solid #ee3124;
        padding: 30px;
        margin-bottom: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .wiki-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(238, 49, 36, 0.1);
    }

    /* כותרת הערך כלינק */
    .item-link {
        color: #1a1a1a !important;
        font-size: 2.2rem;
        font-weight: 700;
        text-decoration: none !important;
        transition: color 0.2s;
        display: block;
        margin-bottom: 10px;
    }
    
    .item-link:hover {
        color: #ee3124 !important;
    }

    /* עיצוב אייטם חדשותי */
    .news-item {
        margin-bottom: 15px;
        padding: 12px 15px;
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #f0f0f0;
        transition: background 0.2s;
    }
    
    .news-item:hover {
        background-color: #fff5f4;
    }

    .source-tag {
        background-color: #ee3124;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
        margin-left: 12px;
        text-transform: uppercase;
    }

    .date-tag {
        color: #999;
        font-size: 0.75rem;
        margin-left: 12px;
    }

    .news-link {
        color: #333 !important;
        font-weight: 600;
        text-decoration: none !important;
        font-size: 1.05rem;
    }

    .views-info {
        background: #f1f3f5;
        color: #495057;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 20px;
    }

    .section-label {
        font-weight: 800;
        color: #1a1a1a;
        font-size: 0.9rem;
        margin-bottom: 15px;
        display: block;
        border-bottom: 2px solid #eee;
        width: fit-content;
        padding-bottom: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def fetch_top_articles():
    for days_back in [1, 2]:
        dt = datetime.now() - timedelta(days=days_back)
        date_str = dt.strftime('%Y/%m/%d')
        display_date = dt.strftime('%d/%m/%Y')
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{date_str}"
        try:
            r = requests.get(url, headers={'User-Agent': 'WikiNews/3.0'}, timeout=10)
            if r.status_code == 200:
                articles = r.json()['items'][0]['articles']
                exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:", "עזרה:", "קטגוריה:", "תבנית:"]
                filtered = [a for a in articles if not any(word in a['article'] for word in exclude)][:20]
                return filtered, display_date
        except: continue
    return [], None

def get_wiki_meta(title):
    encoded_title = urllib.parse.quote(title)
    url = f"https://he.wikipedia.org/w/api.php?action=query&titles={encoded_title}&prop=pageimages|info&format=json&pithumbsize=800"
    try:
        data = requests.get(url, timeout=5).json()
        pages = data.get('query', {}).get('pages', {})
        page = list(pages.values())[0]
        img_url = page.get('thumbnail', {}).get('source', "")
        return {"image": img_url}
    except: return {"image": ""}

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
        
# תצוגה ראשית
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)

top_list, data_date = fetch_top_articles()

if data_date:
    st.markdown(f'<div class="data-status">נכון לנתוני הצפיות של יום {data_date}</div>', unsafe_allow_html=True)

if not top_list:
    st.error("לא ניתן לטעון נתונים. נסה לרענן.")
else:
    for i, art in enumerate(top_list):
        title_clean = art['article'].replace('_', ' ')
        wiki_url = f"https://he.wikipedia.org/wiki/{art['article']}"
        meta = get_wiki_meta(art['article'])
        news = get_google_news(title_clean)
        
        st.markdown(f'<div class="wiki-card">', unsafe_allow_html=True)
        col_img, col_text = st.columns([1, 2.3])
        
        with col_img:
            if meta['image']:
                # עיצוב תמונה עם פינות מעוגלות
                st.markdown(f'<a href="{wiki_url}" target="_blank"><img src="{meta["image"]}" style="width:100%; border-radius:12px; margin-bottom:15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);"></a>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:#f1f3f5; height:200px; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#adb5bd;">אין תמונה בערך</div>', unsafe_allow_html=True)
        
        with col_text:
            st.markdown(f'<div style="color:#ee3124; font-weight:800; font-size: 0.8rem; margin-bottom:5px;">#{i+1} במדד הפופולריות</div>', unsafe_allow_html=True)
            st.markdown(f'<a href="{wiki_url}" target="_blank" class="item-link">{title_clean}</a>', unsafe_allow_html=True)
            st.markdown(f'<div class="views-info">📈 {art["views"]:,} צפיות</div>', unsafe_allow_html=True)
            
            st.markdown('<span class="section-label">למה זה בחדשות?</span>', unsafe_allow_html=True)
            if news:
                for n in news:
                    st.markdown(f"""
                    <div class="news-item">
                        <span class="source-tag">{n['source']}</span>
                        <span class="date-tag">{n['date']}</span>
                        <a href="{n['link']}" target="_blank" class="news-link">{n['title']}</a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.write("לא נמצאו ידיעות רלוונטיות כרגע.")
        
        st.markdown('</div>', unsafe_allow_html=True)
