# Cyber Intelligence Hub (CIH V3.0) - Demo Script

## 1. Opening Statement: The Vision
"Welcome to the demo of Cyber Intelligence Hub V3.0. In an era where data privacy is paramount, CIH provides a **local-first, privacy-aware AI architecture** for cybersecurity threat intelligence. We don't just aggregate news; we process it locally to give you actionable insights without your data ever leaving your infrastructure."

## 2. Architecture: Power of Local AI
"Our stack is built for performance and privacy:
- **Python-powered Pipeline**: Seamless integration from scraper to visualizer.
- **SQLite Backend**: Efficient, local data storage.
- **Ollama + Llama 3**: The heart of our intelligence. We use state-of-the-art local LLMs to categorize threats, analyze sentiment, and extract entities (Attacker, Target, Vulnerability) in real-time."
*Point to `src/processor/train_from_excel.py` or `src/processor/evaluate.py` for AI logic.*

## 3. Data Ingestion: Real-time Scraping
"We monitor the pulse of the cybersecurity world by scraping top-tier sources:
- **BleepingComputer**
- **The Hacker News**
- **Dark Reading**
Our scraper handles duplicate detection and ensures our database is always up-to-date with the latest incident reports."
*Point to `src/scraper/scrape_news.py`.*

## 4. Interactive Visuals: The SOC Experience
"The Dashboard is designed for the modern SOC analyst:
- **Global Threat Map**: Geospatial visualization of incidents using sentiment-based color coding. Red clusters indicate high-severity regions.
- **Cyber Cytoscape (Network Graph)**: Visualizes the relationships between threat actors, targets, and vulnerabilities.
- **Activity Heatmaps & Trends**: Track the volume and sentiment of cyber news over time to identify emerging patterns."
*Point to `src/visualizer/dashboard.py`.*

## 5. Technical Stack: The Engine Behind the Hub
"Our pipeline is powered by a robust set of open-source tools and libraries:
- **Data Ingestion (Scraping & Parsing)**: 
  - `requests` & `BeautifulSoup4`: Robust web scraping of cyber news portals.
  - `feedparser` & `newspaper3k`: High-accuracy RSS and article text extraction.
- **Data Storage & Management**:
  - `SQLAlchemy` (ORM) & `SQLite`: Efficient, local relationship management and persistence.
  - `pandas`: Powering data transformations and duplicate detection.
  - `rapidfuzz`: High-speed fuzzy string matching for identifying similar incident reports.
- **Intelligence & NLP**:
  - **Ollama + Llama 3**: Local-first LLM for advanced sentiment analysis and threat classification.
  - `spacy`: Industry-standard Named Entity Recognition (NER) for extracting attackers, targets, and vulnerabilities.
- **Visualization & UI/UX**:
  - `Dash` (by Plotly): A high-performance web framework for the dashboard UI.
  - `Plotly`: Interactive geospatial maps and time-series charts.
  - `Dash-Cytoscape`: Specialized library for complex network/relationship graphs.
- **Geocoding**:
  - `geopy`: Translating incident locations into geographic coordinates for the SOC map."

## 6. Comparative Edge: Why CIH?
"Why choose CIH over cloud-based alternatives?
- **Zero Data Leakage**: Your intelligence stays on your machine.
- **Cost-Effective**: No API fees for expensive LLM calls.
- **Speed**: Local processing means no network latency for analysis.
- **Total Control**: Custom-tailored models and visualizations for your specific needs."

## 6. Closing
"CIH V3.0 isn't just a tool; it's a private command center for the modern cyber professional. Thank you."
