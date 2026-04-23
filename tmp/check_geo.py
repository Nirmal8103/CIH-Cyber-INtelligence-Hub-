# tmp/check_geo.py
from src.database import SessionLocal, News
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_geo():
    db = SessionLocal()
    total = db.query(News).count()
    with_geo = db.query(News).filter(News.latitude != None).count()
    logger.info(f"Total News: {total}")
    logger.info(f"News with Coordinates: {with_geo}")
    
    if with_geo < total:
        logger.info("Found missing coordinates. Need back-fill.")
    else:
        logger.info("All news have coordinates.")
    db.close()

if __name__ == "__main__":
    check_geo()
