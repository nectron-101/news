import streamlit as st
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import urllib.parse

st.set_page_config(page_title="WikiNews Israel", layout="wide")

# עיצוב CSS משופר למניעת שבירת טקסט
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: rtl; text-align: right; background-color: #f0f2f6; }
    .main-title { color: #ee3124; font-size: 3rem; font-weight: 800; text-align: center; border-bottom: 4px solid #ee3124; }
    .news-card { background: white; padding: 20px; border-right: 6px solid #ee3124; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 25px; border-radius: 4px; }
    .wiki-title { font-size: 1.8rem; font-weight: 700; color: #0056b3; text-decoration: none; }
    .news-box { margin-top: 15px; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }
    .news-item { margin-bottom: 8px; border-bottom: 1px dotted #ccc; padding-bottom: 5px; }
    .news-link { color: #222; text-decoration: none; font-weight: 500; font-size: 1.1rem; display: block; }
    .source-tag { color: #ee3124; font-size: 0.85rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def get_wiki_top_views():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/he.wikipedia/all-access/{yesterday}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WikiNews/1.0'})
        articles = r.json()['items'][0]['articles']
        exclude = ["עמוד_ראשי", "ויקיפדיה:", "מיוחד:", "שיחה:", "קובץ:", "משתמש:"]
        return [a for a in articles if not any(word in a['article'] for word in exclude)][:10]
    except: return []

def get_news(query):
    query = query.replace('_', ' ')
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=he&gl=IL&ceid=IL:he"
    try:
        r = requests.get(url)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall('.//item')[:2]:
            full_title = item.find('title').text
            title = full_title.split(" - ")[0] if " - " in full_title else full_title
            source = item.find('source').text if item.find('source') is not None else "חדשות"
            items.append({"title": title, "link": item.find('link').text, "source": source})
        return items
    except: return []

st.markdown('<h1 class="main-title">WIKI-NEWS ISRAEL</h1>', unsafe_allow_html=True)
st.write("<center>הנושאים הכי מחופשים בישראל והקשרם החדשותי</center>", unsafe_allow_html=True)

data = get_wiki_top_views()

for i, item in enumerate(data):
    name = item['article'].replace('_', ' ')
    news_items = get_news(name)
    
    # בניית ה-HTML בצורה זהירה
    news_html = ""
    if news_items:
        for n in news_items:
            news_html += f"""
            <div class="news-item">
                <span class="source-tag">{n['source']}:</span>
                <a class="news-link" href="{n['link']}" target="_blank">{n['title']}</a>
            </div>
            """
    else:
        news_html = "<p>לא נמצאו כתבות ישירות מהיממה האחרונה.</p>"

    card_template = f"""
    <div class="news-card">
        <div style="color: #666; font-size: 0.9rem;">מקום {i+1} במדד הצפיות</div>
        <a class="wiki-title" href="https://he.wikipedia.org/wiki/{item['article']}" target="_blank">{name}</a>
        <div style="font-size: 0.8rem; color: #999;">{item['views']:,} צפיות אתמול</div>
        <div class="news-box">
            <div style="font-weight: bold; margin-bottom: 10px;">למה זה בחדשות?</div>
            {news_html}
        </div>
    </div>
    """
    st.markdown(card_template, unsafe_allow_html=True)
