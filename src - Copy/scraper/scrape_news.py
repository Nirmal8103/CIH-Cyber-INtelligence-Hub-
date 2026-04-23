# src/scraper/scrape_news.py
from textblob import TextBlob
import feedparser
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.database import SessionLocal, News
from src.processor.classify import classify
from rapidfuzz import fuzz
import logging
import os
from bs4 import BeautifulSoup

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

logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

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

# -----------------------------
# Scrape function
# -----------------------------
def scrape_news():
    db = SessionLocal()

    # Load all existing titles into memory
    existing_titles = [n.title for n in db.query(News.title).all()]
    logging.info(f"Loaded {len(existing_titles)} existing titles into memory.")

    # Get latest article date per source (as datetime.date)
    latest_dates = {}
    for source in [feed["source"] for feed in RSS_FEEDS]:
        latest = db.query(News).filter(News.source == source).order_by(News.date.desc()).first()
        if latest:
            if isinstance(latest.date, datetime):
                latest_dates[source] = latest.date.date()
            else:
                latest_dates[source] = latest.date
        else:
            latest_dates[source] = None

    total_saved = 0
    total_skipped = 0

    for feed in RSS_FEEDS:
        feed_url = feed["url"]
        source_name = feed["source"]
        logging.info(f"Fetching RSS feed: {feed_url}")

        parsed_feed = feedparser.parse(feed_url)
        logging.info(f"Found {len(parsed_feed.entries)} entries in feed: {source_name}")

        for entry in parsed_feed.entries:
            title = entry.title
            link = entry.link
            summary = getattr(entry, "summary", "")

            # Prefer full content if available
            if hasattr(entry, "content") and entry.content:
                text = clean_html(entry.content[0].value)
            else:
                text = clean_html(summary + " " + title)

            # Classification
            category = classify(text)

            published = getattr(entry, "published_parsed", None)
            if published:
                date = datetime(*published[:6]).date()  # keep as date
            else:
                date = datetime.now().date()

            # Skip old articles
            if latest_dates[source_name] and date <= latest_dates[source_name]:
                logging.info(f"SKIPPED (already in DB): {title} [{source_name}]")
                total_skipped += 1
                continue

            # -----------------------------
            # Duplicate detection (title-based)
            # -----------------------------
            duplicate_found = False
            for t in existing_titles:
                if fuzz.token_set_ratio(title, t) > 90:
                    duplicate_found = True
                    break

            if duplicate_found:
                logging.info(f"SKIPPED (duplicate title): {title} [{source_name}]")
                total_skipped += 1
                continue

            # Add to DB
            sentiment = get_sentiment(text)

            news_item = News(
                title=title,
                date=date,
                category=category,
                url=link,
                content=text,
                source=source_name,
                sentiment=sentiment
            )

            try:
                db.add(news_item)
                db.commit()
                logging.info(f"SAVED: {title} [{source_name}]")
                total_saved += 1

                # Update duplicate list in memory
                existing_titles.append(title)

            except IntegrityError:
                db.rollback()
                logging.warning(f"SKIPPED (DB IntegrityError): {title} [{source_name}]")
                total_skipped += 1

            except Exception as e:
                db.rollback()
                logging.error(f"ERROR: {e} - {title} [{source_name}]")
                total_skipped += 1

    db.close()
    logging.info(f"Scraping finished. Total saved: {total_saved}, Total skipped: {total_skipped}")


if __name__ == "__main__":
    scrape_news()
