# /tmp/migrate_db_v3.py
import sqlite3
import os

db_path = "data/news.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE news ADD COLUMN latitude TEXT;")
        cursor.execute("ALTER TABLE news ADD COLUMN longitude TEXT;")
        conn.commit()
        print("Successfully added 'latitude' and 'longitude' columns.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Columns already exist.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
