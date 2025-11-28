# backend/app/services/wassenaar_curation.py
"""
Run this once (or occasionally) to produce a semi-curated JSON index of Wassenaar items.

Usage:
    python -m app.services.wassenaar_curation
This will write backend/app/data/wassenaar_index.json and print top candidates.
"""
import json
import os
from app.config import WASSENAAR_PDF, WASSENAAR_INDEX
from .dual_use_analyzer import DualUseAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_index():
    da = DualUseAnalyzer(pdf_path=WASSENAAR_PDF, cache_json=WASSENAAR_INDEX)
    idx = da.index
    # write again to ensure cache
    try:
        with open(WASSENAAR_INDEX, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        logger.info("Wassenaar index written to %s (%d entries)", WASSENAAR_INDEX, len(idx))
    except Exception as e:
        logger.exception("Failed to write index: %s", e)
    # print a short sample for quick manual curation
    print("=== SAMPLE WASSENAAR CANDIDATES (first 40) ===")
    for i, it in enumerate(idx[:40]):
        print(f"[{i}] {it.get('text')[:300]}")
        print("   keywords:", it.get("keywords"))
        print()

if __name__ == "__main__":
    build_index()
