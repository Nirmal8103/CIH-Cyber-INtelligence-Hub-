import sqlite3
db = sqlite3.connect('data/news.db')
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables in database:", [t[0] for t in tables])
for t in tables:
    table_name = t[0]
    print(f"\nSchema for {table_name}:")
    schema = db.execute(f"PRAGMA table_info({table_name});").fetchall()
    for col in schema:
        print(f"  - {col[1]} ({col[2]})")
