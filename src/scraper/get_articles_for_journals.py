from src.database import SessionLocal, News

def fetch_articles_for_journal(limit=10):
    """
    Fetch latest N articles from the News table
    and convert them into journal-ready dictionaries.
    """
    db = SessionLocal()

    # Get latest articles
    rows = (
        db.query(News)
        .order_by(News.date.desc())
        .limit(limit)
        .all()
    )

    articles = []
    for row in rows:
        articles.append({
            "title": row.title,
            "source": row.source,
            "published": row.date.isoformat(),
            "content": row.content
        })

    db.close()
    return articles
