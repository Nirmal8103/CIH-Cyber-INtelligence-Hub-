# src/processor/train_from_excel.py
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import pickle
import os
import logging

# -----------------------------
# Setup logging
# -----------------------------
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "train.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# -----------------------------
# Paths
# -----------------------------
EXCEL_FILE = "data/cyber_news.xlsx"  # your Excel file path
CLASSIFIER_FILE = "src/processor/news_classifier.pkl"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# -----------------------------
# Load dataset
# -----------------------------
logging.info(f"Loading dataset from {EXCEL_FILE}")
df = pd.read_excel(EXCEL_FILE)

# Combine Title + Article for training
df["text"] = df["Title"].fillna("") + " " + df["Article"].fillna("")
train_texts = df["text"].tolist()
train_labels = df["Label"].tolist()
logging.info(f"Loaded {len(train_texts)} articles")

# -----------------------------
# Generate embeddings
# -----------------------------
logging.info(f"Loading embedding model: {EMBEDDING_MODEL}")
embedder = SentenceTransformer(EMBEDDING_MODEL)
logging.info("Generating embeddings...")
embeddings = embedder.encode(train_texts, show_progress_bar=True)

# -----------------------------
# Train classifier
# -----------------------------
logging.info("Training classifier...")
clf = LogisticRegression(max_iter=2000)
clf.fit(embeddings, train_labels)

# -----------------------------
# Save classifier
# -----------------------------
os.makedirs(os.path.dirname(CLASSIFIER_FILE), exist_ok=True)
with open(CLASSIFIER_FILE, "wb") as f:
    pickle.dump(clf, f)
logging.info(f"Classifier saved to {CLASSIFIER_FILE}")
print("[INFO] Training complete and classifier saved.")
