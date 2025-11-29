# backend/app/services/enhanced_data_fetcher.py
import os
import json
import requests
from typing import Dict, List, Any, Optional
from app.config import NEWSAPI_KEY, TIM_EXPORT, ASPI_EXPORT, DATA_DIR
import time
from datetime import datetime
import logging
import re
import asyncio

logger = logging.getLogger(__name__)

# country detection helpers
try:
    import pycountry
    _COUNTRY_NAMES = [c.name for c in pycountry.countries]
except Exception:
    _COUNTRY_NAMES = [
        "United States","China","India","United Kingdom","Germany","Japan","South Korea",
        "France","Canada","Israel","Singapore","Australia","Brazil","Russia","Netherlands"
    ]

class EnhancedDataFetcher:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.crossref_base = "https://api.crossref.org/works"
        self.europepmc_base = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        self.newsapi_key = NEWSAPI_KEY or self.config.get("newsapi_key", "")
        # lazy TIM/ASPI
        try:
            from app.services.tim_data_fetcher import TIMDataFetcher
            from app.services.aspi_data_fetcher import ASPIDataFetcher
            self.tim_fetcher = TIMDataFetcher(self.config.get("tim_export") or TIM_EXPORT)
            self.aspi_fetcher = ASPIDataFetcher(self.config.get("aspi_export") or ASPI_EXPORT)
        except Exception as e:
            logger.info("TIM/ASPI fetchers not initialized: %s", e)
            self.tim_fetcher = None
            self.aspi_fetcher = None

        # domain synonyms / keywords (expandable)
        self.domain_keyword_map = {
            "Artificial Intelligence": ["artificial intelligence", "ai", "machine learning", "deep learning", "neural network", "transformer", "nlp", "computer vision"],
            "Biotechnology": ["biotechnology", "bio", "biological", "genetic", "crispr", "gene editing", "vaccine"],
            "Quantum Computing": ["quantum computing", "qubit", "quantum"],
            "Space Technology": ["satellite", "rocket", "spacecraft", "launch", "satcom"],
            "Robotics": ["robotics", "robot", "uav", "drone", "autonomous vehicle"],
            "Cybersecurity": ["cybersecurity", "encryption", "cryptography", "malware", "vulnerability"]
        }

    async def fetch_country_tech_data(self, country: str, domain: str, years_back: Optional[int] = None, extra_sources: Optional[List[str]] = None, original_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Async wrapper. Runs the blocking network operations in a thread so you can await it.
        Returns a dict: publications, patents, news, tim, aspi, raw_text, extra_sources
        """
        return await asyncio.to_thread(self._sync_fetch_country_tech_data, country, domain, years_back, extra_sources or [], original_domain)

    def _sync_fetch_country_tech_data(self, country: str, domain: str, years_back: Optional[int], extra_sources: List[str], original_domain: Optional[str]) -> Dict[str, Any]:
        results = {"publications": [], "patents": [], "news": [], "tim": [], "aspi": [], "raw_text": [], "extra_sources": []}

        # build expanded queries from domain map (deduplicate). If domain matches known keys use their synonyms
        keywords = []
        # try exact domain key match (case-insensitive)
        key_match = None
        for k in self.domain_keyword_map:
            if k.lower() == domain.lower():
                key_match = k
                break
        if key_match:
            keywords = [domain] + [kw for kw in self.domain_keyword_map.get(key_match, []) if kw not in [domain]]
        else:
            # if custom domain string (multilingual) just use it as single keyword
            keywords = [domain]

        seen_urls = set()

        # Query CrossRef for each keyword variant
        for kw in keywords:
            q = f"{kw} {country}"
            try:
                cr = self._fetch_crossref(q, years_back)
                for item in cr:
                    item["detected_countries"] = self._detect_countries_in_item(item, country)
                    url = item.get("url")
                    if url and url in seen_urls:
                        continue
                    seen_urls.add(url)
                    results["publications"].append(item)
            except Exception as e:
                logger.exception("CrossRef fetch error for query %s: %s", q, e)

        # Europe PMC one pass (broad)
        try:
            ep = self._fetch_europepmc(f"{domain} {country}", years_back)
            for item in ep:
                item["detected_countries"] = self._detect_countries_in_item(item, country)
                url = item.get("url")
                if url and url in seen_urls:
                    continue
                seen_urls.add(url)
                results["publications"].append(item)
        except Exception as e:
            logger.exception("EuropePMC fetch error: %s", e)

        # TIM & ASPI if present (use their local fetchers)
        if self.tim_fetcher:
            try:
                tim_items = self.tim_fetcher.fetch_tim_items(country, domain, years_back)
                for it in tim_items:
                    it["detected_countries"] = self._detect_countries_in_item(it, country)
                    results["tim"].append(it)
            except Exception as e:
                logger.exception("TIM fetch error: %s", e)

        if self.aspi_fetcher:
            try:
                aspi_items = self.aspi_fetcher.fetch_aspi_items(country, domain, years_back)
                for it in aspi_items:
                    it["detected_countries"] = self._detect_countries_in_item(it, country)
                    results["aspi"].append(it)
            except Exception as e:
                logger.exception("ASPI fetch error: %s", e)

        # NewsAPI (optional)
        if self.newsapi_key:
            try:
                news = self._fetch_newsapi(f"{domain} {country}", years_back)
                for it in news:
                    it["detected_countries"] = self._detect_countries_in_item(it, country)
                    results["news"].append(it)
            except Exception as e:
                logger.exception("NewsAPI fetch error: %s", e)

        # patents stub (EPO OPS could be added here if you have credentials)
        try:
            patents = self._fetch_patents_stub(f"{domain} {country}", years_back)
            for p in patents:
                p["detected_countries"] = self._detect_countries_in_item(p, country)
                results["patents"].append(p)
        except Exception as e:
            logger.exception("Patents fetch stub failed: %s", e)

        # add any extra_sources provided by user
        if extra_sources:
            for s in extra_sources:
                results["extra_sources"].append({"source": s, "note": "user_provided"})
                results["raw_text"].append(str(s))

        # local publications fallback (if present in DATA_DIR/publications.json)
        try:
            local_pub = f"{DATA_DIR}/publications.json"
            if local_pub and isinstance(local_pub, str) and os.path.exists(local_pub):
                with open(local_pub, "r", encoding="utf-8") as f:
                    pubs = json.load(f)
                filtered = []
                for it in pubs if isinstance(pubs, list) else [pubs]:
                    txt = " ".join([str(it.get(k, "")).lower() for k in ("title", "abstract", "description")])
                    if country.lower() in txt or (domain and domain.lower() in txt) or (original_domain and original_domain.lower() in txt):
                        filtered.append(it)
                results["publications"].extend(filtered[:200])
        except Exception as e:
            logger.exception("Failed to load local publications: %s", e)

        # news.json fallback
        try:
            news_file = f"{DATA_DIR}/news.json"
            if os.path.exists(news_file):
                with open(news_file, "r", encoding="utf-8") as f:
                    news_items = json.load(f)
                filtered = []
                for it in news_items if isinstance(news_items, list) else [news_items]:
                    txt = (it.get("title","") + " " + it.get("summary","") + " " + it.get("description","")).lower()
                    if country.lower() in txt or (domain and domain.lower() in txt) or (original_domain and original_domain.lower() in txt):
                        filtered.append(it)
                results["news"].extend(filtered[:200])
        except Exception as e:
            logger.exception("Failed to load news.json: %s", e)

        # raw_text: collect representative text for analyzer scanning
        for k in ("publications","patents","news","tim","aspi"):
            for it in results.get(k, [])[:200]:
                s = " ".join([str(it.get(x,"")) for x in ("title","abstract","summary","description") if it.get(x)])
                if s:
                    results["raw_text"].append(s)

        # fallback: if nothing at all, add a minimal note
        if not any([results[k] for k in ("publications","tim","aspi","news")]):
            results["raw_text"].append(f"No local items found for {country} / domain '{domain}'. Consider adding extra sources.")

        return results

    def _fetch_crossref(self, query: str, years_back: Optional[int] = None, rows=50) -> List[Dict]:
        params = {"query.bibliographic": query, "rows": rows, "sort": "relevance"}
        if years_back:
            year_from = datetime.now().year - int(years_back) + 1
            params["filter"] = f"from-pub-date:{year_from}"
        try:
            r = requests.get(self.crossref_base, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.exception("CrossRef request failed: %s", e)
            return []

        out = []
        for item in data.get("message", {}).get("items", []):
            pub_year = None
            try:
                if item.get("issued", {}).get("date-parts"):
                    pub_year = item["issued"]["date-parts"][0][0]
            except Exception:
                pub_year = None
            affiliations = []
            authors = item.get("author", []) or []
            for a in authors:
                affs = a.get("affiliation") or []
                if isinstance(affs, list):
                    for af in affs:
                        if isinstance(af, dict):
                            affiliations.append(af.get("name"))
                        else:
                            affiliations.append(str(af))
                elif isinstance(affs, dict):
                    affiliations.append(affs.get("name"))
            out.append({
                "title": (item.get("title") or [""])[0],
                "year": pub_year,
                "url": item.get("URL"),
                "source": "crossref",
                "abstract": (item.get("abstract") or "")[:3000],
                "affiliations": affiliations
            })
        return out

    def _fetch_europepmc(self, query: str, years_back: Optional[int] = None, pageSize=25) -> List[Dict]:
        params = {"query": query, "format": "json", "pageSize": pageSize}
        if years_back:
            year_from = datetime.now().year - int(years_back) + 1
            params["query"] = f"{query} AFTER_YEAR:{year_from}"
        try:
            r = requests.get(self.europepmc_base, params=params, timeout=20)
            r.raise_for_status()
            d = r.json()
        except Exception as e:
            logger.exception("EuropePMC request failed: %s", e)
            return []

        out = []
        for rec in d.get("resultList", {}).get("result", []):
            pub_year = None
            try:
                if rec.get("pubYear"):
                    pub_year = int(rec.get("pubYear"))
            except:
                pub_year = None
            out.append({
                "title": rec.get("title"),
                "year": pub_year,
                "url": rec.get("id"),
                "source": "europepmc",
                "abstract": rec.get("abstractText") or "",
                "affiliations": rec.get("authorAffiliations") or []
            })
        return out

    def _fetch_newsapi(self, query: str, years_back: Optional[int] = None, pageSize=50) -> List[Dict]:
        base = "https://newsapi.org/v2/everything"
        params = {"q": query, "pageSize": pageSize, "apiKey": self.newsapi_key}
        if years_back:
            params["from"] = f"{datetime.now().year - int(years_back)}-01-01"
        try:
            r = requests.get(base, params=params, timeout=20)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            logger.exception("NewsAPI request failed: %s", e)
            return []

        out = []
        for art in j.get("articles", []):
            pub_year = None
            if art.get("publishedAt"):
                try:
                    pub_year = int(art["publishedAt"][:4])
                except:
                    pub_year = None
            out.append({
                "title": art.get("title"),
                "year": pub_year,
                "url": art.get("url"),
                "source": art.get("source", {}).get("name"),
                "abstract": art.get("description") or ""
            })
        return out

    def _fetch_patents_stub(self, query: str, years_back: Optional[int] = None) -> List[Dict]:
        # placeholder: if you add EPO OPS credentials, implement here.
        return []

    def _detect_countries_in_item(self, item: Dict[str, Any], country_hint: Optional[str] = None) -> List[str]:
        text_to_search = " ".join(filter(None, [
            item.get("title", ""),
            item.get("abstract", ""),
            " ".join(item.get("affiliations", []) if isinstance(item.get("affiliations"), list) else [item.get("affiliations","")])
        ])).lower()

        found = set()
        if country_hint and country_hint.lower() in text_to_search:
            found.add(country_hint)

        for cname in _COUNTRY_NAMES:
            try:
                if cname.lower() in text_to_search:
                    found.add(cname)
            except Exception:
                continue
        return list(found)
