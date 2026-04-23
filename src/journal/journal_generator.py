"""
journal_generator.py

Features:
- generate_summary(text): extractive summary using summa (TextRank)
- extract_keywords(text, top_n=6): keyword extraction (summa or spaCy fallback)
- generate_reflection(summary, keywords, local_llm_url=None): uses local LLM if provided, else uses template-driven reflection
- generate_journal_pdf(...): builds a PDF with cover + journal entries (reportlab)
- fetch_articles_for_journal(limit): fetches latest articles from DB in dict format for journal generation

Usage examples at bottom.
"""

import os
import math
import json
from datetime import datetime
from dateutil import tz
import requests

# Summarizer + keywords
from summa.summarizer import summarize
from summa import keywords as summa_keywords

# PDF generation
from reportlab.lib.pagesizes import LETTER, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame, Spacer

# Optional spaCy enrichment (if installed)
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

# -------------------------
# Database fetch helper
# -------------------------
from src.database import SessionLocal, News

def fetch_articles_for_journal(limit=10):
    """
    Pull latest N records from News table and convert to
    journal-ready dictionaries expected by
    generate_journal_entries_from_articles().
    """
    db = SessionLocal()
    rows = (
        db.query(News)
        .order_by(News.date.desc())
        .limit(limit)
        .all()
    )

    articles = []
    for r in rows:
        articles.append({
            "title": r.title,
            "source": r.source,
            "published": (
                r.date.isoformat() if hasattr(r.date, "isoformat") else str(r.date)
            ),
            "content": r.content
        })
    db.close()
    return articles

# -------------------------
# Text cleaning helpers
# -------------------------
def clean_text(text: str) -> str:
    """Basic cleaning: remove excessive whitespace and control chars."""
    if not text:
        return ""
    t = text.replace("\r", "\n")
    while "\n\n" in t:
        t = t.replace("\n\n", "\n")
    t = " ".join(t.split())
    return t.strip()

# -------------------------
# Summarization
# -------------------------
def generate_summary(text: str, ratio: float = 0.15, words: int = None) -> str:
    text = clean_text(text)
    if words:
        total_words = len(text.split())
        if total_words == 0:
            return ""
        ratio = max(0.05, min(0.5, words / total_words))
    try:
        s = summarize(text, ratio=ratio)
        if not s or len(s.split()) < 12:
            s = summarize(text, ratio=min(0.33, ratio*2))
    except Exception:
        s = " ".join(text.split()[:120])
    return s.strip()

# -------------------------
# Keyword extraction
# -------------------------
def extract_keywords(text: str, top_n: int = 6) -> list:
    text = clean_text(text)
    try:
        kw_text = summa_keywords.keywords(text, split=True, scores=False)
        if kw_text:
            return [k for k in kw_text[:top_n]]
    except Exception:
        pass

    if nlp:
        doc = nlp(text)
        candidates = [token.lemma_.lower() for token in doc
                      if token.pos_ in ("NOUN", "PROPN") and not token.is_stop and token.is_alpha]
        freq = {}
        for c in candidates:
            freq[c] = freq.get(c, 0) + 1
        sorted_kw = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in sorted_kw[:top_n]]

    words = [w.lower() for w in text.split() if len(w) > 3]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_kw = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [k for k, _ in sorted_kw[:top_n]]

# -------------------------
# Local LLM invoke (LM Studio / Ollama style)
# -------------------------
def call_local_llm(prompt: str, endpoint_url: str, timeout: int = 30) -> str:
    headers = {"Content-Type": "application/json"}
    body = {
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0.2,
    }
    try:
        resp = requests.post(endpoint_url, headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            if "choices" in data and len(data["choices"]) > 0:
                ch = data["choices"][0]
                if isinstance(ch.get("message"), dict):
                    return ch["message"].get("content", "") or ch.get("text", "")
                return ch.get("text", "")
            if "result" in data:
                return data["result"]
            if "content" in data:
                return data["content"]
        return resp.text
    except Exception as e:
        print(f"[local_llm] request error: {e}")
        return ""

# -------------------------
# Reflection generation
# -------------------------
def template_reflection(summary: str, keywords: list) -> str:
    summary = clean_text(summary)
    k = ", ".join(keywords[:4]) if keywords else "critical areas"
    lower = summary.lower()
    angle = "risk"
    if any(term in lower for term in ("ransomware", "ransom", "encrypt")):
        angle = "ransomware"
    elif any(term in lower for term in ("phishing", "credential", "social engineering")):
        angle = "phishing"
    elif any(term in lower for term in ("vulnerability", "zero-day", "exploit")):
        angle = "vulnerability"
    elif any(term in lower for term in ("supply chain", "third-party", "vendor")):
        angle = "supply_chain"

    templates = {
        "ransomware": (
            "This article highlights ongoing ransomware threats and their potential operational impact. "
            "Organizations should prioritize offline backups, segmentation, and tested incident response playbooks. "
            "Key topics extracted: {keys}. Immediate steps include threat hunting and validating backups. "
            "Overall, this incident underscores the continued importance of resilience and rapid detection."
        ),
        "phishing": (
            "The article underscores social engineering trends and phishing techniques. "
            "It reinforces that user awareness, strong MFA, and email filtering remain crucial defenses. "
            "Key topics extracted: {keys}. Organizations should test phishing simulation programs and update detection rules. "
            "This news reiterates how human vectors remain a primary attack surface."
        ),
        "vulnerability": (
            "This event focuses on vulnerabilities and exploit chaining. Timely patching, vulnerability scanning, "
            "and threat intelligence are critical. Key topics extracted: {keys}. Organizations must prioritize exposure reduction "
            "and compensating controls until patches are applied."
        ),
        "supply_chain": (
            "Supply-chain risks are emphasized by this article. Vetting third parties, monitoring for anomalous behavior, "
            "and restricting privileges are key mitigations. Key topics extracted: {keys}. This emphasizes governance around vendors."
        ),
        "risk": (
            "This article highlights important cybersecurity concerns and operational implications. Key topics extracted: {keys}. "
            "From a pragmatic perspective, organizations should evaluate their controls, enhance detection, and ensure incident readiness. "
            "This underscores the need for continuous monitoring and proactive risk management."
        ),
    }

    return templates.get(angle, templates["risk"]).format(keys=k)

def generate_reflection(summary: str, keywords: list, local_llm_url: str = None) -> str:
    if local_llm_url:
        prompt = (
            "You are a cybersecurity analyst. Based on the following summary, write a professional "
            "reflection paragraph (5-7 sentences) that covers: key insights, why it matters, implications "
            "for organizations, lessons learned, and a short recommendation.\n\n"
            f"Summary:\n{summary}\n\nKeywords: {', '.join(keywords[:8])}\n\nReflection:"
        )
        resp = call_local_llm(prompt, local_llm_url)
        if resp and len(resp.strip()) > 20:
            return resp.strip()
    return template_reflection(summary, keywords)

# -------------------------
# PDF generation (reportlab)
# -------------------------
def _add_paragraph(flow_frame, text, style):
    p = Paragraph(text.replace("\n", "<br/>"), style)
    flow_frame.addFromList([p], flow_frame._canvas)

def generate_journal_pdf(
    journal_title: str,
    prepared_by: str,
    submitted_to: str,
    entries: list,
    output_path: str = "cyber_journal.pdf",
    header_text: str = "",
    footer_text: str = "",
    page_size=A4,
    author_name_on_pages: str = None,
):
    c = canvas.Canvas(output_path, pagesize=page_size)
    width, height = page_size
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    # --- Cover page ---
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 2 * inch, journal_title)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 2.6 * inch, f"Prepared by: {prepared_by}")
    c.drawCentredString(width / 2, height - 2.9 * inch, f"Submitted to: {submitted_to}")
    c.drawCentredString(width / 2, height - 3.2 * inch, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    c.showPage()

    left_margin = inch * 0.75
    right_margin = width - inch * 0.75
    usable_width = right_margin - left_margin
    top = height - inch * 0.75
    bottom = inch * 0.75

    for idx, e in enumerate(entries):
        if header_text:
            c.setFont("Helvetica", 9)
            c.drawString(left_margin, height - 0.5 * inch, header_text)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_margin, top - 0.0 * inch, e.get("title", f"Article {idx+1}"))
        c.setFont("Helvetica", 9)
        meta_line = f"Source: {e.get('source','unknown')}  |  Published: {e.get('published','unknown')}"
        c.drawString(left_margin, top - 0.35 * inch, meta_line)

        frame_top = top - 0.8 * inch
        frame_height = frame_top - bottom
        frame = Frame(left_margin, bottom + 0.5 * inch, usable_width, frame_height, showBoundary=0)

        flow = []
        flow.append(Paragraph("<b>Summary</b>", styles["Heading3"]))
        flow.append(Paragraph(e.get("summary",""), normal))
        flow.append(Spacer(1, 8))
        flow.append(Paragraph("<b>Reflection</b>", styles["Heading3"]))
        flow.append(Paragraph(e.get("reflection",""), normal))
        frame.addFromList(flow, c)

        if footer_text:
            c.setFont("Helvetica-Oblique", 8)
            c.drawCentredString(width / 2, 0.5 * inch, footer_text)

        if author_name_on_pages:
            c.setFont("Helvetica", 8)
            c.drawRightString(right_margin, 0.55 * inch, f"{author_name_on_pages} - Page {idx+2}")

        c.showPage()

    c.save()
    return output_path

# -------------------------
# High-level generator
# -------------------------
def generate_journal_entries_from_articles(articles: list, local_llm_url: str = None, summary_words: int = None):
    entries = []
    for article in articles:
        text = article.get("content") or article.get("body") or ""
        summary = generate_summary(text, words=summary_words)
        keywords = extract_keywords(text)
        reflection = generate_reflection(summary, keywords, local_llm_url=local_llm_url)
        entries.append({
            "title": article.get("title", "Untitled"),
            "source": article.get("source", ""),
            "published": article.get("published", ""),
            "summary": summary,
            "reflection": reflection,
            "keywords": keywords,
            "content": text
        })
    return entries

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    # 1. Fetch latest articles from DB
    articles = fetch_articles_for_journal(limit=10)

    # 2. Local LLM optional
    local_llm_url = None  # or "http://localhost:1234/v1/chat/completions"

    # 3. Create structured journal entries
    entries = generate_journal_entries_from_articles(
        articles,
        local_llm_url=local_llm_url,
    )

    # 4. Generate PDF
    output = generate_journal_pdf(
        journal_title="Daily Cybersecurity Journal",
        prepared_by="Nirmal Thapa",
        submitted_to="Internal Review",
        entries=entries,
        output_path="daily_cyber_journal.pdf",
        header_text="Cyber News Journal - Confidential",
        footer_text="Prepared by Nirmal Thapa - Internal Use Only",
        author_name_on_pages="Nirmal Thapa",
    )

    print("Generated:", output)
