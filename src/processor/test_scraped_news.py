# src/processor/test_scraped_news.py
from src.database import SessionLocal, News
from src.processor.classify import classify

db = SessionLocal()
news_items = db.query(News).all()
db.close()

print(f"Total news items: {len(news_items)}\n")

# Test first N items
N = 20
for n in news_items[:N]:
    predicted = classify(n.content)
    print(f"Title: {n.title}")
    print(f"Source: {n.source}")
    print(f"Saved Category: {n.category}")
    print(f"Predicted Category: {predicted}")
    print(f"Match: {'✅' if predicted == n.category else '❌'}")
    print("-" * 60)
