# backend/app/services/news_fetcher.py
import os
import logging
import requests
import feedparser
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional: use newspaper3k for full content extraction when scraping article page
try:
    from newspaper import Article as NewspaperArticle
    NEWSPAPER_AVAILABLE = True
except Exception:
    NEWSPAPER_AVAILABLE = False

class NewsFetcher:
    def __init__(self, api_key: Optional[str] = None, rss_sources: Optional[List[str]] = None, timeout: int = 12):
        self.api_key = api_key
        # a small default set of RSS feeds useful across regions. You can extend this list in config.
        self.default_rss = rss_sources or [
            "https://www.reutersagency.com/feed/?best-topics=technology&post_type=best",
            "https://www.bbc.co.uk/feeds/rss/world/business/rss.xml",
            "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
            "https://www.theguardian.com/world/rss",
            "https://feeds.feedburner.com/TechCrunch/"
        ]
        self.timeout = timeout

    def fetch_news(self, query: str, years_back: Optional[int] = None, max_items: int = 30) -> List[Dict[str, Any]]:
        """
        Try NewsAPI first (if api_key present). If no key, fallback to RSS scraping + optional page extraction.
        Returns list of {title, url, description, publishedAt, source, year}.
        """
        out = []
        if self.api_key:
            try:
                base = "https://newsapi.org/v2/everything"
                params = {"q": query, "pageSize": max_items, "apiKey": self.api_key}
                if years_back:
                    params["from"] = f"{__import__('datetime').datetime.now().year - int(years_back)}-01-01"
                r = requests.get(base, params=params, timeout=self.timeout)
                r.raise_for_status()
                j = r.json()
                for art in j.get("articles", []):
                    year = None
                    if art.get("publishedAt"):
                        try:
                            year = int(art["publishedAt"][:4])
                        except:
                            year = None
                    out.append({
                        "title": art.get("title"),
                        "url": art.get("url"),
                        "description": art.get("description") or "",
                        "source": (art.get("source") or {}).get("name"),
                        "publishedAt": art.get("publishedAt"),
                        "year": year
                    })
                return out
            except Exception as e:
                logger.info("NewsAPI fetch failed, falling back to RSS: %s", e)

        # Fallback: RSS feed scraping + naive filtering by query words
        feeds = self.default_rss
        q_terms = [w.strip().lower() for w in query.split() if len(w.strip()) > 2]
        found = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:max_items]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description","")
                    url = entry.get("link")
                    text_lower = (title + " " + summary).lower()
                    if all(term in text_lower for term in q_terms[:3]) or any(term in text_lower for term in q_terms[:1]):
                        year = None
                        if entry.get("published"):
                            try:
                                year = int(entry.published[:4])
                            except:
                                year = None
                        item = {"title": title, "url": url, "description": summary, "source": feed_url, "publishedAt": entry.get("published"), "year": year}
                        # optionally enrich with newspaper3k article text
                        if NEWSPAPER_AVAILABLE and url:
                            try:
                                a = NewspaperArticle(url)
                                a.download()
                                a.parse()
                                item["content"] = a.text[:4000]
                            except Exception:
                                pass
                        found.append(item)
            except Exception as e:
                logger.info("RSS feed parsing failed for %s: %s", feed_url, e)
            if len(found) >= max_items:
                break
        # dedupe by url/title
        seen = set()
        out = []
        for f in found:
            uid = f.get("url") or f.get("title")
            if uid in seen: continue
            seen.add(uid)
            out.append(f)
            if len(out) >= max_items:
                break
        return out
