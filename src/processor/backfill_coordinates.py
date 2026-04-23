"""
Coordinate backfill script with retry logic.
For articles that have no lat/lon, find their GPE entities and attempt geocoding.
Respects Nominatim 429 Rate Limits by backing off for 5 seconds.
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database import SessionLocal, News, Entity
from src.processor.geocoder import get_coordinates
from sqlalchemy.orm import joinedload

def backfill_coordinates():
    db = SessionLocal()
    try:
        # Get articles missing coordinates
        all_articles = db.query(News).options(joinedload(News.entities)).all()
        no_coords = [a for a in all_articles if not a.latitude or a.latitude == 'None']

        total = len(no_coords)
        print(f"Articles missing coordinates: {total}")

        geocoded = 0
        skipped = 0
        rate_limits = 0

        for i, article in enumerate(no_coords):
            gpe_entities = [e.name for e in article.entities if e.type == 'GPE']

            if not gpe_entities:
                skipped += 1
                continue

            lat, lon = None, None
            for gpe in gpe_entities:
                # Try geocoding up to 3 times if we hit 429
                for attempt in range(3):
                    from geopy.exc import GeocoderInsufficientPrivileges
                    try:
                        lat, lon = get_coordinates(gpe)
                        if lat:
                            break
                    except Exception as e:
                        if '429' in str(e):
                            rate_limits += 1
                            print(f"  [Rate Limit] Backing off 5 seconds... ({gpe})")
                            time.sleep(5)
                            continue
                        break # Other errors, give up on this entity
                    
                if lat:
                    break
                time.sleep(1.5)  # Normal delay

            if lat:
                article.latitude = str(lat)
                article.longitude = str(lon)
                db.commit()
                geocoded += 1
            else:
                skipped += 1

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{total} checked... ({geocoded} newly geocoded)")

        print(f"\nCoordinate backfill complete.")
        print(f"  Newly geocoded: {geocoded} articles")
        print(f"  Skipped (no GPE or unresolvable): {skipped}")
        print(f"  Times rate-limited: {rate_limits}")

        # Final count
        from sqlalchemy import text
        with_coords = db.execute(text("SELECT COUNT(*) FROM news WHERE latitude IS NOT NULL AND latitude != 'None'")).scalar()
        print(f"  Total articles with coordinates: {with_coords}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    backfill_coordinates()
