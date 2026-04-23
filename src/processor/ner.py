# src/processor/ner.py
import spacy
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load Spacy model lazily
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.info("Spacy model 'en_core_web_sm' loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Spacy model: {e}")
    return _nlp

CVE_REGEX = r"CVE-\d{4}-\d{4,7}"

def extract_entities(text):
    """
    Extract named entities from text.
    Returns a comma-separated string of entity names (for backwards compatibility).
    """
    results = extract_entities_with_types(text)
    return ", ".join(sorted([r["name"] for r in results]))

def extract_entities_with_types(text):
    """
    Extract named entities with their types.
    Returns a list of dicts: [{"name": "Microsoft", "type": "ORG"}, ...]
    Entity types: CVE, ORG, PRODUCT, GPE
    """
    if not text:
        return []

    nlp = get_nlp()
    results = {}

    # 1. Regex for CVEs
    cves = re.findall(CVE_REGEX, text, re.IGNORECASE)
    for cve in cves:
        name = cve.upper()
        results[name] = "CVE"

    # 2. spaCy for ORG, PRODUCT, GPE
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "GPE"]:
                clean_name = ent.text.strip().replace("\n", " ")
                if len(clean_name) > 2 and clean_name not in results:
                    results[clean_name] = ent.label_

    return [{"name": name, "type": etype} for name, etype in results.items()]

def extract_gpe_entities(text):
    """Return only geographic entities (GPE) for geocoding."""
    return [r["name"] for r in extract_entities_with_types(text) if r["type"] == "GPE"]

if __name__ == "__main__":
    sample = "Microsoft and Google reported CVE-2024-1234 affecting cloud services in Washington, D.C."
    print(extract_entities_with_types(sample))
