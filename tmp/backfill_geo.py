# tmp/backfill_geo.py
from src.database import SessionLocal, News
from src.processor.geocoder import get_coordinates
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill():
    db = SessionLocal()
    # Find articles without coordinates
    from sqlalchemy.orm import joinedload
    pending = db.query(News).options(joinedload(News.entities)).filter(News.latitude == None).all()
    logger.info(f"Backfilling {len(pending)} articles...")
    
    updated = 0
    for article in pending:
        # Try to find a location in entities (List of Entity objects)
        if article.entities:
            for entity_obj in article.entities:
                entity = entity_obj.name
                # Basic heuristic: if it's not a CVE and not too long, try geocoding it
                if not entity.upper().startswith("CVE-") and len(entity) < 50:
                    lat, lon = get_coordinates(entity)
                    if lat and lon:
                        article.latitude = lat
                        article.longitude = lon
                        updated += 1
                        # Throttle to respect Nominatim usage policy if not cached
                        time.sleep(1) 
                        break # Found one location, move to next article
        
        # If no entities yielded coordinates, try the source or title (optional, keeping it simple for now)
        if not article.latitude:
            # Maybe the source is a location?
            if article.source and len(article.source) < 30:
                lat, lon = get_coordinates(article.source)
                if lat and lon:
                    article.latitude = lat
                    article.longitude = lon
                    updated += 1
                    time.sleep(1)

    db.commit()
    logger.info(f"Backfill complete. Updated {updated} articles.")
    db.close()

if __name__ == "__main__":
    backfill()
