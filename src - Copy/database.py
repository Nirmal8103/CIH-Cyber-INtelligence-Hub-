# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    
    title = Column(String(300), unique=True, nullable=False)
    date = Column(DateTime)
    category = Column(String(100))
    url = Column(String(300), nullable=False)
    content = Column(Text)
    source = Column(String(100), nullable=False)
    sentiment = Column(String(20)) 

    def __repr__(self):
        return f"<News(title='{self.title}', category='{self.category}', date='{self.date}')>"

engine = create_engine("sqlite:///data/news.db")
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
