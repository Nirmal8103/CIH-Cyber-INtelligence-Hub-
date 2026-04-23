# tmp/backfill_alerts.py
from src.database import SessionLocal, News, AlertRule, AlertHistory
from src.processor.alerts import check_article_alerts
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill():
    db = SessionLocal()
    articles = db.query(News).all()
    logger.info(f"Scanning {len(articles)} articles for alert triggers...")
    
    # Clear old history to avoid duplicates during backfill if any
    db.query(AlertHistory).delete()
    db.commit()
    
    for article in articles:
        check_article_alerts(article)
    
    count = db.query(AlertHistory).count()
    logger.info(f"Backfill complete. Generated {count} live alerts.")
    db.close()

if __name__ == "__main__":
    backfill()
