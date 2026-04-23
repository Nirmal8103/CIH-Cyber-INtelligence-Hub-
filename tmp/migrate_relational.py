# /tmp/migrate_relational.py
import sqlite3
import os
import shutil

DB_PATH = "data/news.db"
BACKUP_PATH = "data/news_backup.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    # 1. Backup existing DB
    shutil.copyfile(DB_PATH, BACKUP_PATH)
    print(f"Backup created at {BACKUP_PATH}")

    # 2. Connect
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. Rename old table temporarily
    cursor.execute("ALTER TABLE news RENAME TO news_old;")

    # 4. Create new tables
    cursor.execute("""
        CREATE TABLE news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(500) NOT NULL,
            date DATE NOT NULL,
            category VARCHAR(50),
            url VARCHAR(500) UNIQUE NOT NULL,
            content TEXT,
            source VARCHAR(100) NOT NULL,
            sentiment VARCHAR(20),
            ai_summary TEXT,
            latitude TEXT,
            longitude TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) UNIQUE NOT NULL,
            type VARCHAR(50)
        );
    """)
    cursor.execute("""
        CREATE TABLE article_entity (
            article_id INTEGER,
            entity_id INTEGER,
            PRIMARY KEY (article_id, entity_id),
            FOREIGN KEY (article_id) REFERENCES news (id),
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        );
    """)

    # 5. Migrate base news data
    cursor.execute("""
        INSERT INTO news (id, title, date, category, url, content, source, sentiment, ai_summary, latitude, longitude)
        SELECT id, title, date, category, url, content, source, sentiment, ai_summary, latitude, longitude FROM news_old;
    """)

    # 6. Migrate entities from CSV string
    cursor.execute("SELECT id, entities FROM news_old WHERE entities IS NOT NULL AND entities != '';")
    rows = cursor.fetchall()
    
    for row in rows:
        article_id, entity_str = row
        entities = [e.strip() for e in entity_str.split(',') if e.strip()]
        
        for entity_name in entities:
            # Insert unique entity
            cursor.execute("INSERT OR IGNORE INTO entities (name, type) VALUES (?, ?);", (entity_name, None))
            # Get entity ID
            cursor.execute("SELECT id FROM entities WHERE name = ?;", (entity_name,))
            entity_id = cursor.fetchone()[0]
            # Link them
            cursor.execute("INSERT OR IGNORE INTO article_entity (article_id, entity_id) VALUES (?, ?);", (article_id, entity_id))

    # 7. Clean up
    cursor.execute("DROP TABLE news_old;")
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
