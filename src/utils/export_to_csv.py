import csv
from src.database import SessionLocal, News

def export_news_to_csv(output_file="data/news_export.csv"):
    db = SessionLocal()

    rows = db.query(
        News.title,
        News.date,
        News.url,
        News.source,
        News.sentiment
    ).all()

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # header
        writer.writerow(["title", "date", "url", "source", "sentiment"])

        # data
        for row in rows:
            writer.writerow(row)

    db.close()
    print(f"✅ Exported {len(rows)} rows to {output_file}")

if __name__ == "__main__":
    export_news_to_csv()
