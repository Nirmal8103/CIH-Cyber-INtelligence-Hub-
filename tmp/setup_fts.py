# /tmp/setup_fts.py
import sqlite3
import os

DB_PATH = "data/news.db"

def setup_fts():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create FTS5 table
        cursor.execute("DROP TABLE IF EXISTS news_fts;")
        cursor.execute("""
            CREATE VIRTUAL TABLE news_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                ai_summary,
                tokenize='porter'
            );
        """)

        # Initial population
        cursor.execute("""
            INSERT INTO news_fts (id, title, content, ai_summary)
            SELECT id, title, content, ai_summary FROM news;
        """)
        
        # Create triggers to keep FTS in sync
        cursor.execute("DROP TRIGGER IF EXISTS news_ai;")
        cursor.execute("""
            CREATE TRIGGER news_ai AFTER INSERT ON news BEGIN
                INSERT INTO news_fts (id, title, content, ai_summary)
                VALUES (new.id, new.title, new.content, new.ai_summary);
            END;
        """)

        conn.commit()
        print("Successfully set up FTS5 search index and triggers.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_fts()
