# /tmp/cleanup_dates.py
import sqlite3
import os

db_path = "data/news.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Select all dates
        cursor.execute("SELECT id, date FROM news;")
        rows = cursor.fetchall()
        for row in rows:
            idx, date_str = row
            if date_str and " " in date_str:
                new_date = date_str.split(" ")[0]
                cursor.execute("UPDATE news SET date = ? WHERE id = ?;", (new_date, idx))
        conn.commit()
        print("Successfully sanitized dates.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database {db_path} not found.")
