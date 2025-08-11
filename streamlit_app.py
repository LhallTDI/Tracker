import re
from datetime import datetime
import requests
import feedparser
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Multi-RSS PubMed Summarizer", page_icon="📚", layout="wide")
st.title("📚 Multi-RSS PubMed Summarizer")

# -------- Helper functions
@st.cache_data(ttl=60 * 10)
def fetch_feed(url: str):
    try:
        r = requests.get(url, headers={"User-Agent": "StreamlitRSS/1.0"}, timeout=15)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        return {"error": str(e), "entries": []}

def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()

def summarize_to_bullets(text: str, max_points: int = 3) -> str:
    clean = strip_html(text)
    sentences = re.split(r'(?<=[.!?]) +', clean)
    bullets = [f"• {s}" for s in sentences if s][:max_points]
    return "\n".join(bullets)

def safe_get(entry, field, default=""):
    return entry.get(field) or entry.get(f"{field}_detail", {}).get("value") or default

# -------- Define your feeds
feeds = {
    "Ultra Processed Food": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1DYWH3zMZmlfY-F0ZFitZ_oQWzovDyXzKMHAjArSqxPDxYYsYv/?limit=5",
    "Drugs": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1DYWH3zMZmlfY-F0ZFitZ_oQWzovDyXzKMHAjArSqxPDxYYsYv/?limit=5",
    "Manufacturing": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1DYWH3zMZmlfY-F0ZFitZ_oQWzovDyXzKMHAjArSqxPDxYYsYv/?limit=5",
}

# -------- Collect all results
all_rows = []
for category, url in feeds.items():
    feed = fetch_feed(url)
    if isinstance(feed, dict) and feed.get("error"):
        st.error(f"Error fetching {category}: {feed['error']}")
        continue

    for entry in getattr(feed, "entries", []):
        title = safe_get(entry, "title", "Untitled")
        link = safe_get(entry, "link", "")
        summary = safe_get(entry, "summary", "")
        journal = safe_get(entry, "source", "Unknown journal")
        bullet_summary = summarize_to_bullets(summary)

        all_rows.append({
            "Category": category,
            "Journal": journal,
            "Title": f"[{title}]({link})",
            "Summary": bullet_summary
        })

# -------- Convert to DataFrame & show
if all_rows:
    df = pd.DataFrame(all_rows)
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No results found for any feed.")
