# backend/app/services/tim_data_fetcher.py
import json
import os
from typing import List, Dict, Optional
from app.config import TIM_EXPORT

class TIMDataFetcher:
    """
    Reads a TIM DU local export (JSON) and normalizes records.
    If TIM_EXPORT file does not exist, returns empty list.
    """
    def __init__(self, export_path: Optional[str] = None):
        self.export_path = export_path or TIM_EXPORT
        self._data = None
        if os.path.exists(self.export_path):
            try:
                with open(self.export_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = None

    def fetch_tim_items(self, country: str, domain: str, years_back: Optional[int] = None) -> List[Dict]:
        if not self._data:
            return []
        out = []
        for item in self._data:
            countries = item.get("countries", []) or []
            title = item.get("title") or item.get("name") or ""
            year = item.get("year") or item.get("pubYear") or None
            categories = item.get("categories") or item.get("domains") or []
            # simple matching heuristics
            if domain and domain.lower() not in " ".join(categories).lower() and domain.lower() not in title.lower():
                # domain doesn't match; still allow if country matches
                if country and country not in countries and country.lower() not in title.lower():
                    continue
            if country:
                if (isinstance(countries, list) and country not in countries) and (country.lower() not in title.lower()):
                    # skip if country mismatch
                    # allow TIM items without explicit country if domain matches strongly
                    pass
            if years_back and year:
                import datetime
                if int(year) < datetime.datetime.now().year - int(years_back) + 1:
                    continue
            out.append({
                "title": title,
                "year": year,
                "url": item.get("url") or item.get("link"),
                "source": "tim",
                "abstract": item.get("abstract") or item.get("summary") or "",
                "raw": item
            })
        return out
