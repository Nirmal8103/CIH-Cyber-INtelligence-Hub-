# /tmp/migrate_db_v2.py
import sqlite3
import os

db_path = "data/news.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN ai_summary TEXT;")
        conn.commit()
        print("Successfully added 'ai_summary' column to 'news' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'ai_summary' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
