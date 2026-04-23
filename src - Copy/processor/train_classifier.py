# src/processor/train_classifier.py
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import pickle
import os

from .train_data import train_texts, train_labels

MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight CPU-friendly embeddings
CLASSIFIER_FILE = "src/processor/news_classifier.pkl"

# Load embedding model
embedder = SentenceTransformer(MODEL_NAME)

# Encode training data
embeddings = embedder.encode(train_texts)

# Train classifier
clf = LogisticRegression(max_iter=1000)
clf.fit(embeddings, train_labels)

# Save classifier
with open(CLASSIFIER_FILE, "wb") as f:
    pickle.dump(clf, f)

print(f"[INFO] Classifier trained and saved to {CLASSIFIER_FILE}")
