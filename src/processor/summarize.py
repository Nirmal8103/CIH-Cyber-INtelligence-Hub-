# src/processor/summarize.py
import requests
import json
import logging
import threading

ai_lock = threading.Lock()

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

def summarize_article(text):
    """
    Summarize a cybersecurity article using Ollama and Llama 3.
    """
    if not text:
        return ""

    prompt = (
        "You are a cybersecurity expert. Summarize the following news article in exactly ONE concise sentence. "
        "Focus on the main threat, target, and impact. Avoid fluff.\n\n"
        f"Article: {text[:2000]}"
    )

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        with ai_lock:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        logger.info("Successfully generated AI summary.")
        return summary
    except Exception as e:
        logger.error(f"Error during AI summarization: {e}")
        return text[:200] + "..."  # fallback to simple slice

if __name__ == "__main__":
    test_text = "Microsoft has released a patch for a critical zero-day vulnerability in Windows that was being exploited by state-sponsored actors to gain remote access."
    print(f"Summary: {summarize_article(test_text)}")
