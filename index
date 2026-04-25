import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

# הגדרות דף ועיצוב CSS בסגנון YNET
st.set_page_config(page_title="WikiNews Israel", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
        background-color: #f6f6f6;
    }
    
    .main-title {
        color: #ee3124;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0;
        border-bottom: 4px solid #ee3124;
        padding-bottom: 10px;
    }
    
    .subtitle {
        text-align: center;
        color: #333;
        margin-bottom: 30px;
    }

    .news-card {
        background: white;
        padding: 20px;
        border-radius: 0px;
        border-right: 5px solid #ee3124;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    .wiki-rank {
        color: #ee3124;
        font-weight: bold;
        font-size: 1.2rem;
    }

    .wiki-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #222;
        text-decoration: none;
        margin-bottom: 10px;
        display: block;
    }
    
    .wiki-title:hover {
        color: #ee3124;
    }

    .views-tag {
        background: #eee;
        padding: 2px 8px;
        font-size: 0.9rem;
        border-radius: 4px;
        color: #666;
    }

    .news-box {
        margin-top: 15px;
        padding-top: 15px;
        border-top: 1px solid #eee;
    }

    .news-item {
        margin-bottom: 10px;
        padding-right: 15px;
        position: relative;
    }

    .news-item::before {
        content: "●";
        color: #ee3124;
        position: absolute;
        right: 0;
    }

    .news-link {
        color: #0056b3;
        text-decoration: none;
        font-weight: 400;
        font-size: 1.1rem;
    }

    .news-link:hover {
        text-decoration: underline;
    }

    .source-tag {
        color: #999;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# פונקציות שליפת הנתונים
def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    headers = {'User-Agent': 'WikiNewsProject/1.0'}
    try:
        response = requests.get(url, headers=headers)
        articles = response.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:"]
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:10]
    except:
        return []

def get_news(query):
    query = query.replace('_', ' ')
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        root = ET.fromstring(requests.get(url).content)
        items = []
        for item in root.findall('.//item')[:2]:
            items.append({
                "title": item.find('title').text.split(" - ")[0],
                "link": item.find('link').text,
                "source": item.find('source').text if item.find('source') is not None else "חדשות"
            })
        return items
    except:
        return []

# בניית הממשק
st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">הנושאים הכי חמים בישראל על פי ויקיפדיה והקשרם החדשותי</p>', unsafe_allow_html=True)

data = get_wiki_top_views()

if not data:
    st.warning("טוען נתונים... (או שהשירות של ויקיפדיה אינו זמין)")
else:
    for i, item in enumerate(data):
        article_name = item['article'].replace('_', ' ')
        views = item['views']
        news_items = get_news(article_name)
        
        # יצירת כרטיס לכל אייטם
        card_html = f"""
        <div class="news-card">
            <span class="wiki-rank">#{i+1} במדד הפופולריות</span>
            <a class="wiki-title" href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank">{article_name}</a>
            <span class="views-tag">{views:,} צפיות אתמול</span>
            
            <div class="news-box">
                <strong>למה זה בחדשות?</strong>
        """
        
        if news_items:
            for n in news_items:
                card_html += f"""
                <div class="news-item">
                    <a class="news-link" href="{n['link']}" target="_blank">{n['title']}</a>
                    <span class="source-tag">| {n['source']}</span>
                </div>
                """
        else:
            card_html += "<p>לא נמצאו ידיעות ישירות, כנראה מדובר בחיפוש כללי או אישיות מוכרת.</p>"
            
        card_html += "</div></div>"
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<br><br><center style='color:#999'>הנתונים נשלפים בזמן אמת מוויקיפדיה וחדשות גוגל</center>", unsafe_allow_html=True)
