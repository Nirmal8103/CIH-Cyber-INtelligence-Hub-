# src/processor/classify.py
import os
import pickle
import logging
from sentence_transformers import SentenceTransformer

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------
# Paths and model
# -----------------------------
CLASSIFIER_FILE = "src/processor/news_classifier.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"

# Load embedding model
logger.info(f"Loading embedding model: {MODEL_NAME}")
embedder = SentenceTransformer(MODEL_NAME)

# Load classifier
def load_classifier():
    if os.path.exists(CLASSIFIER_FILE):
        with open(CLASSIFIER_FILE, "rb") as f:
            clf = pickle.load(f)
        logger.info(f"Loaded classifier from {CLASSIFIER_FILE}")
        return clf
    else:
        logger.warning(f"Classifier file not found: {CLASSIFIER_FILE}")
    return None

clf = load_classifier()

# -----------------------------
# Classification functions
# -----------------------------
def classify(text):
    """
    Classify a single article text.
    Returns predicted label or 'other' if classifier is not loaded.
    """
    if not text or text.strip() == "":
        return "other"

    if clf is None:
        return "other"

    try:
        embedding = embedder.encode([text], normalize_embeddings=True)
        pred = clf.predict(embedding)
        return pred[0]
    except Exception as e:
        logger.error(f"Classification error: {e}")
        return "other"


def classify_batch(texts):
    """
    Classify a list of article texts.
    Returns a list of predicted labels.
    """
    if clf is None:
        return ["other"] * len(texts)

    cleaned_texts = [
        t if t and t.strip() != "" else "other"
        for t in texts
    ]

    try:
        embeddings = embedder.encode(
            cleaned_texts,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        preds = clf.predict(embeddings)
        return preds.tolist()
    except Exception as e:
        logger.error(f"Batch classification error: {e}")
        return ["other"] * len(texts)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    sample_text = "Microsoft Exchange suffers a critical vulnerability exploited in the wild."
    prediction = classify(sample_text)
    print(f"Predicted label: {prediction}")
