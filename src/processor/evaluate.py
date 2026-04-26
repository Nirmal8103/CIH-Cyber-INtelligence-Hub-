# src/processor/evaluate.py
import pandas as pd
from src.database import SessionLocal, News, Entity
import logging

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_evaluation(df=None):
    """
    Perform a quantitative analysis of the intelligence system's performance.
    If df is provided, evaluate based on that dataframe (local frame).
    Otherwise, evaluate the entire database (global).
    """
    if df is not None:
        return calculate_metrics_from_df(df)
    
    db = SessionLocal()
    try:
        articles = db.query(News).all()
        entities = db.query(Entity).all()
        
        total_articles = len(articles)
        total_entities = len(entities)
        
        if total_articles == 0:
            return {"status": "error", "message": "No data."}
            
        avg_entities = sum(len(a.entities) for a in articles) / total_articles
        avg_orig_len = sum(len(a.content) for a in articles if a.content) / total_articles
        avg_sum_len = sum(len(a.ai_summary) for a in articles if a.ai_summary) / total_articles
        compression_ratio = avg_sum_len / avg_orig_len if avg_orig_len > 0 else 0
        ner_cov = sum(1 for a in articles if a.entities) / total_articles

        return {
            "metrics": {
                "total_intelligence_nodes": total_articles + total_entities,
                "avg_entity_density": round(avg_entities, 2),
                "compression_efficiency": f"{round(compression_ratio * 100, 1)}%",
                "ner_coverage": f"{round(ner_cov * 100, 1)}%"
            }
        }
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return None
    finally:
        db.close()

def calculate_metrics_from_df(df):
    """Calculate metrics from a filtered dataframe."""
    if df.empty:
        return {"metrics": {"total_intelligence_nodes": 0, "avg_entity_density": 0, "compression_efficiency": "0%", "ner_coverage": "0%"}}
    
    df = df.copy()
    total_articles = len(df)
    
    # Estimate entity count from the entities string column
    def count_ents(s):
        if not s or pd.isna(s): return 0
        return len([e for e in s.split(',') if e.strip()])
    
    df['ent_count'] = df['entities'].apply(count_ents)
    avg_entities = df['ent_count'].mean()
    
    total_unique_ents = len(set([e.strip() for sublist in df['entities'].dropna().str.split(',') for e in sublist if e.strip()]))
    
    # Compression
    avg_orig_len = df['content'].str.len().mean() if 'content' in df.columns else 1
    avg_sum_len = df['ai_summary'].str.len().mean() if 'ai_summary' in df.columns else 0
    compression_ratio = avg_sum_len / avg_orig_len if avg_orig_len > 0 else 0
    
    ner_cov = len(df[df['ent_count'] > 0]) / total_articles

    return {
        "metrics": {
            "total_intelligence_nodes": total_articles + total_unique_ents,
            "avg_entity_density": round(avg_entities, 2),
            "compression_efficiency": f"{round(compression_ratio * 100, 1)}%",
            "ner_coverage": f"{round(ner_cov * 100, 1)}%"
        }
    }

if __name__ == "__main__":
    run_evaluation()
