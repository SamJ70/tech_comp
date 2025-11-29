# backend/app/services/arxiv_fetcher.py
import feedparser, logging
from typing import List, Dict
logger = logging.getLogger(__name__)

ARXIV_BASE = "http://export.arxiv.org/api/query"

class ArxivFetcher:
    def __init__(self, timeout=15):
        self.timeout = timeout

    def search(self, query: str, max_results: int = 25) -> List[Dict]:
        q = f"all:{query}"
        url = f"{ARXIV_BASE}?search_query={q}&start=0&max_results={max_results}"
        try:
            feed = feedparser.parse(url)
            out = []
            for entry in feed.entries:
                authors = [a.name for a in entry.authors] if hasattr(entry, "authors") else []
                year = None
                if hasattr(entry, "published"):
                    try:
                        year = int(entry.published[:4])
                    except:
                        year = None
                out.append({
                    "title": entry.title,
                    "year": year,
                    "url": entry.link,
                    "source": "arxiv",
                    "abstract": (entry.summary or "")[:3000],
                    "authors": authors
                })
            return out
        except Exception as e:
            logger.info("arXiv fetch failed: %s", e)
            return []
