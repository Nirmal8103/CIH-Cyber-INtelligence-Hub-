# tmp/check_alerts.py
from src.database import SessionLocal, AlertRule, AlertHistory, News
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def audit_alerts():
    db = SessionLocal()
    rules = db.query(AlertRule).count()
    history = db.query(AlertHistory).count()
    news = db.query(News).count()
    
    logger.info(f"Total Alert Rules: {rules}")
    logger.info(f"Total Alert History Entries: {history}")
    logger.info(f"Total News Articles: {news}")
    
    if rules == 0:
        logger.info("No alert rules found. Seeding default rules...")
        default_rules = [
            AlertRule(name="Critical CVE Detected", target_category="Vulnerability", keywords="CVE-", is_active=1),
            AlertRule(name="Ransomware Outbreak", keywords="Ransomware,LockBit,Conti", is_active=1),
            AlertRule(name="State-Sponsored Activity", keywords="APT,China,Russia,Iran,North Korea", is_active=1),
            AlertRule(name="Zero-Day Alert", keywords="Zero-day,0-day,unpatched", is_active=1)
        ]
        db.add_all(default_rules)
        db.commit()
        logger.info("Default rules seeded.")
    
    db.close()

if __name__ == "__main__":
    audit_alerts()
