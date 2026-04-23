# src/processor/test_classifier.py
from sentence_transformers import SentenceTransformer
import pickle
from .train_data import train_texts, train_labels

MODEL_NAME = "all-MiniLM-L6-v2"
CLASSIFIER_FILE = "src/processor/news_classifier.pkl"

# Load the trained classifier
with open(CLASSIFIER_FILE, "rb") as f:
    clf = pickle.load(f)

# Load embedding model
embedder = SentenceTransformer(MODEL_NAME)

# Test on some example texts
examples = [
    "A new ransomware is spreading across Europe affecting hospitals",
    "Critical zero-day vulnerability discovered in Windows",
    "Phishing emails target customers of major banks",
]

# Encode examples
embeddings = embedder.encode(examples)

# Predict categories
predictions = clf.predict(embeddings)

for text, category in zip(examples, predictions):
    print(f"[PREDICTED] {category} -> {text}")
