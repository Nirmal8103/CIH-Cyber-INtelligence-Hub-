# src/scraper/scrape_news.py
from textblob import TextBlob
import feedparser
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.database import SessionLocal, News, Entity
from src.processor.classify import classify
from src.processor.ner import extract_entities, extract_entities_with_types, extract_gpe_entities
from src.processor.summarize import summarize_article
from src.processor.geocoder import get_coordinates
from src.processor.alerts import check_article_alerts
from rapidfuzz import fuzz
import logging
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# -----------------------------
# News Sentiment
# -----------------------------
def get_sentiment(text):
    if not text:
        return "Neutral"
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# -----------------------------
# Setup logging
# -----------------------------
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "scraper.log")

logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a"),
        logging.StreamHandler()
    ]
)

# -----------------------------
# RSS Feeds
# -----------------------------
RSS_FEEDS = [
    {"url": "https://feeds.feedburner.com/TheHackersNews", "source": "The Hacker News"},
    {"url": "https://www.csoonline.com/feed/", "source": "CSO Online"},
    {"url": "https://threatpost.com/feed/", "source": "ThreatPost"},
    {"url": "https://www.darkreading.com/rss.xml", "source": "Dark Reading"},
    {"url": "https://krebsonsecurity.com/feed/", "source": "Krebs on Security"},
    {"url": "https://www.bleepingcomputer.com/feed/", "source": "BleepingComputer"},
    {"url": "https://www.schneier.com/blog/atom.xml", "source": "Schneier on Security"},
]

# -----------------------------
# Utility: clean HTML
# -----------------------------
def clean_html(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def process_feed(feed, limit_per_feed, existing_titles, existing_urls):
    """Worker function to process a single feed in a thread."""
    db = SessionLocal()
    saved_in_this_feed = 0
    source_name = feed["source"]
    feed_url = feed["url"]
    
    try:
        logging.info(f"THREAD START: Fetching {source_name}")
        parsed_feed = feedparser.parse(feed_url)
        
        for entry in parsed_feed.entries:
            if saved_in_this_feed >= limit_per_feed:
                break
                
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '')
            
            # Duplicate detection
            if link in existing_urls or title in existing_titles:
                continue
                
            # Extract date
            published = getattr(entry, "published_parsed", None)
            if published:
                date = datetime(*published[:6]).date()
            else:
                date = datetime.now().date()

            # Content extraction
            summary = getattr(entry, "summary", "")
            if hasattr(entry, "content") and entry.content:
                text = clean_html(entry.content[0].value)
            else:
                text = clean_html(summary + " " + title)

            # AI Processing
            category = classify(text)
            entity_data = extract_entities_with_types(text)
            ai_summary = summarize_article(text)

            # Geocode
            lat, lon, loc_name = None, None, None
            for gpe in extract_gpe_entities(text):
                lat, lon = get_coordinates(gpe)
                if lat:
                    loc_name = gpe
                    break

            # Sentiment
            sentiment = get_sentiment(text)

            news_item = News(
                title=title,
                date=date,
                category=category,
                url=link,
                content=text,
                source=source_name,
                sentiment=sentiment,
                ai_summary=ai_summary,
                latitude=str(lat) if lat else None,
                longitude=str(lon) if lon else None,
                location_name=loc_name
            )
            
            # Handle entities
            for ent_name, ent_type in entity_data:
                entity = db.query(Entity).filter_by(name=ent_name).first()
                if not entity:
                    entity = Entity(name=ent_name, type=ent_type)
                    db.add(entity)
                    db.flush()
                if entity not in news_item.entities:
                    news_item.entities.append(entity)

            db.add(news_item)
            saved_in_this_feed += 1
            logging.info(f"THREAD SAVE: [{source_name}] {title[:50]}...")

        db.commit()
    except Exception as e:
        logging.error(f"THREAD ERROR in {source_name}: {e}")
        db.rollback()
    finally:
        db.close()
    
    return saved_in_this_feed

# -----------------------------
# Scrape function (Parallel Engine)
# -----------------------------
def scrape_news(limit=14):
    """
    Main entry point. Uses threads to fetch from all sources at once.
    'limit' here is used to calculate per-feed balance.
    Default 14 means ~2 articles per feed (if 7 feeds).
    """
    db = SessionLocal()
    # Load existing to avoid thread collisions on duplicates
    existing_titles = {n.title for n in db.query(News.title).all()}
    existing_urls = {n.url for n in db.query(News.url).all()}
    db.close()

    num_feeds = len(RSS_FEEDS)
    limit_per_feed = max(1, limit // num_feeds)
    if limit % num_feeds > 0:
        limit_per_feed += 1
    
    total_saved = 0
    logging.info(f"STARTING PARALLEL SCRAPE: {num_feeds} sources, ~{limit_per_feed} per source.")

    with ThreadPoolExecutor(max_workers=num_feeds) as executor:
        futures = {executor.submit(process_feed, feed, limit_per_feed, existing_titles, existing_urls): feed for feed in RSS_FEEDS}
        
        for future in as_completed(futures):
            feed = futures[future]
            try:
                count = future.result()
                total_saved += count
            except Exception as e:
                logging.error(f"Feed {feed['source']} generated an exception: {e}")

    logging.info(f"PARALLEL SCRAPE COMPLETE: Total {total_saved} articles saved.")
    return total_saved

if __name__ == "__main__":
    scrape_news(limit=20)
