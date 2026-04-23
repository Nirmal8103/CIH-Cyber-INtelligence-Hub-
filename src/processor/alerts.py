# src/processor/alerts.py
import logging
from src.database import AlertRule, AlertHistory, SessionLocal
from datetime import datetime

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def check_article_alerts(article):
    """
    Check if a news article triggers any active alert rules.
    """
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(AlertRule.is_active == 1).all()
        for rule in rules:
            match = True
            
            # Category match
            if rule.target_category and rule.target_category.lower() != article.category.lower():
                match = False
            
            # Sentiment match
            if match and rule.sentiment_threshold and rule.sentiment_threshold.lower() != article.sentiment.lower():
                match = False
                
            # Keyword match
            if match and rule.keywords:
                keywords = [k.strip().lower() for k in rule.keywords.split(',')]
                content_lower = article.content.lower() if article.content else ""
                title_lower = article.title.lower()
                if not any(k in title_lower or k in content_lower for k in keywords):
                    match = False
            
            if match:
                logger.warning(f"!!! ALERT TRIGGERED: '{rule.name}' for article '{article.title}'")
                alert = AlertHistory(
                    article_id=article.id,
                    rule_id=rule.id,
                    timestamp=datetime.now().date()
                )
                db.add(alert)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error processing alerts: {e}")
        db.rollback()
    finally:
        db.close()

def seed_default_rules():
    """
    Seed some useful cybersecurity alert rules.
    """
    db = SessionLocal()
    try:
        if db.query(AlertRule).count() == 0:
            rules = [
                AlertRule(name="Critical Ransomware Alert", target_category="Ransomware", sentiment_threshold="Negative"),
                AlertRule(name="Zero-Day Vulnerability", keywords="zero-day, 0-day, patched"),
                AlertRule(name="State-Sponsored Threat", keywords="APT, state-sponsored, nation-state"),
                AlertRule(name="Data Breach/Leak", target_category="Data Breach", sentiment_threshold="Negative")
            ]
            db.add_all(rules)
            db.commit()
            logger.info("Seeded default alert rules.")
    except Exception as e:
        logger.error(f"Error seeding rules: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    from src.database import init_db
    init_db()
    seed_default_rules()
