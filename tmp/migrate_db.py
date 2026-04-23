# /tmp/migrate_db.py
import sqlite3
import os

db_path = "data/news.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN entities TEXT;")
        conn.commit()
        print("Successfully added 'entities' column to 'news' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'entities' already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found. It will be created with the new schema when the app runs.")
