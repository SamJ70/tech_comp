# backend/app/services/aspi_data_fetcher.py
import json
import os
from typing import Dict, List, Optional
from app.config import ASPI_EXPORT

class ASPIDataFetcher:
    """
    Read ASPI TechTracker export if available and normalize.
    If the export is not present, returns empty.
    """
    def __init__(self, export_path: Optional[str] = None):
        self.export_path = export_path or ASPI_EXPORT
        self._data = None
        if os.path.exists(self.export_path):
            try:
                with open(self.export_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = None

    def fetch_aspi_items(self, country: str, domain: str, years_back: Optional[int] = None) -> List[Dict]:
        if not self._data:
            return []
        out = []
        for item in self._data:
            title = item.get("title") or item.get("name") or ""
            year = item.get("year") or item.get("pubYear") or None
            countries = item.get("countries") or item.get("country") or []
            if isinstance(countries, str):
                countries = [countries]
            # simple matching heuristics
            if country and country not in countries and country.lower() not in title.lower():
                continue
            if domain and domain.lower() not in title.lower() and domain.lower() not in (item.get("category") or "").lower():
                continue
            if years_back and year:
                import datetime
                if int(year) < datetime.datetime.now().year - int(years_back) + 1:
                    continue
            out.append({
                "title": title,
                "year": year,
                "url": item.get("url") or item.get("link"),
                "source": "aspi",
                "abstract": item.get("summary") or "",
                "raw": item
            })
        return out
