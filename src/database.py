# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# -----------------------------
# Database setup
# -----------------------------
DB_URL = "sqlite:///data/news.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Link table for Many-to-Many Article <-> Entity
article_entity_association = Table(
    'article_entity',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('news.id'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True)
)

class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    type = Column(String(50))  # CVE, ORG, PRODUCT, GPE

    articles = relationship("News", secondary=article_entity_association, back_populates="entities")

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    date = Column(Date, nullable=False)
    category = Column(String(50))
    url = Column(String(500), unique=True, nullable=False)
    content = Column(Text)
    source = Column(String(100), nullable=False)
    sentiment = Column(String(20))
    ai_summary = Column(Text)
    latitude = Column(Text)
    longitude = Column(Text)
    location_name = Column(String(200))

    # Many-to-Many
    entities = relationship("Entity", secondary=article_entity_association, back_populates="articles")

    def __repr__(self):
        return f"<News(title='{self.title}', category='{self.category}', date='{self.date}')>"

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    target_category = Column(String(100))
    sentiment_threshold = Column(String(20))
    keywords = Column(String(500))  # comma-separated
    is_active = Column(Integer, default=1)

class AlertHistory(Base):
    __tablename__ = "alert_history"
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news.id'))
    rule_id = Column(Integer, ForeignKey('alert_rules.id'))
    timestamp = Column(Date)

    article = relationship("News")
    rule = relationship("AlertRule")

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    Base.metadata.create_all(bind=engine)
