"""
Entity backfill script.
Re-runs NER on all articles that have no linked entities and writes results to the DB.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.database import SessionLocal, News, Entity
from src.processor.ner import extract_entities_with_types
from sqlalchemy.orm import joinedload

def backfill_entities():
    db = SessionLocal()
    try:
        # Get all articles that have no linked entities
        all_articles = db.query(News).options(joinedload(News.entities)).all()
        articles_to_process = [a for a in all_articles if not a.entities]
        
        total = len(articles_to_process)
        print(f"Articles to backfill: {total}")
        
        updated = 0
        skipped = 0

        for i, article in enumerate(articles_to_process):
            text = article.content or article.title or ""
            if not text.strip():
                skipped += 1
                continue

            entity_data = extract_entities_with_types(text)
            if not entity_data:
                skipped += 1
                continue

            for ent in entity_data:
                name = ent['name'].strip()
                if not name:
                    continue
                db_entity = db.query(Entity).filter(Entity.name == name).first()
                if not db_entity:
                    db_entity = Entity(name=name, type=ent['type'])
                    db.add(db_entity)
                    db.flush()
                elif not db_entity.type:
                    db_entity.type = ent['type']
                
                if db_entity not in article.entities:
                    article.entities.append(db_entity)

            db.commit()
            updated += 1

            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{total} articles processed...")

        print(f"\nBackfill complete.")
        print(f"  Updated: {updated} articles")
        print(f"  Skipped (no content/entities): {skipped}")

        # Final count
        from sqlalchemy import text
        join_count = db.execute(text('SELECT COUNT(*) FROM article_entity')).scalar()
        total_entities = db.query(Entity).count()
        print(f"  Total entities in DB: {total_entities}")
        print(f"  Total article-entity links: {join_count}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    backfill_entities()
