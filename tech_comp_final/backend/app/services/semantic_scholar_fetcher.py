# backend/app/services/semantic_scholar_fetcher.py
import requests, logging
from typing import List, Dict, Optional
logger = logging.getLogger(__name__)

class SemanticScholarFetcher:
    BASE = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, timeout=15):
        self.timeout = timeout

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,authors,abstract,url,citationCount,venue"
        }
        try:
            r = requests.get(self.BASE, params=params, timeout=self.timeout)
            r.raise_for_status()
            j = r.json()
            out = []
            for it in j.get("data", []):
                out.append({
                    "title": it.get("title"),
                    "year": it.get("year"),
                    "url": it.get("url"),
                    "source": "semanticscholar",
                    "abstract": it.get("abstract") or "",
                    "citationCount": it.get("citationCount"),
                    "authors": [a.get("name") for a in it.get("authors", [])]
                })
            return out
        except Exception as e:
            logger.info("SemanticScholar fetch failed: %s", e)
            return []
