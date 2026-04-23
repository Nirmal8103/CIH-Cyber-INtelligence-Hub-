# src/processor/evaluate_classifier.py
from src.database import SessionLocal, News
from src.processor.classify import classify
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def evaluate_classifier(show_misclassified=True):
    db = SessionLocal()
    news_list = db.query(News).all()
    db.close()

    if not news_list:
        print("[INFO] No news in database to evaluate.")
        return

    df = pd.DataFrame({
        "title": [n.title for n in news_list],
        "content": [n.content for n in news_list],
        "category": [n.category for n in news_list],
        "source": [n.source for n in news_list]
    })

    y_true = df["category"].tolist()
    y_pred = [classify(text) for text in df["content"]]

    acc = accuracy_score(y_true, y_pred)
    print(f"[INFO] Classifier Accuracy: {acc*100:.2f}%\n")

    print("[INFO] Classification Report:")
    print(classification_report(y_true, y_pred))

    if show_misclassified:
        df["predicted"] = y_pred
        misclassified = df[df["predicted"] != df["category"]]
        if misclassified.empty:
            print("\n[INFO] All news classified correctly!")
        else:
            print(f"\n[INFO] Misclassified articles ({len(misclassified)}):")
            for idx, row in misclassified.iterrows():
                print(f"\nTitle: {row['title']}")
                print(f"Source: {row['source']}")
                print(f"Actual: {row['category']}, Predicted: {row['predicted']}")
                print(f"Content: {row['content'][:200]}...")  # show first 200 chars

if __name__ == "__main__":
    evaluate_classifier()
