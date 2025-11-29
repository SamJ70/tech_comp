# backend/app/services/wassenaar_curation.py
"""
Run this once (or occasionally) to produce a semi-curated JSON index of Wassenaar items.

Usage:
    python -m app.services.wassenaar_curation
This will write backend/app/data/wassenaar_parsed.json and print top candidates.
"""
import json
import logging
import os
from app.services.wassenaar_parser import parse_wassenaar
from app.config import WASSENAAR_PDF, WASSENAAR_INDEX

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_index():
    # parse and get categories map
    idx = parse_wassenaar(pdf_path=WASSENAAR_PDF, cache_path=WASSENAAR_INDEX)
    # write again (parse_wassenaar already caches, but ensure file exists)
    try:
        os.makedirs(os.path.dirname(WASSENAAR_INDEX), exist_ok=True)
        with open(WASSENAAR_INDEX, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        logger.info("Wassenaar index written to %s (%d categories)", WASSENAAR_INDEX, len(idx))
    except Exception as e:
        logger.exception("Failed to write index: %s", e)

    print("=== SAMPLE WASSENAAR CATEGORIES (first 40 keys) ===")
    keys = list(idx.keys())[:40]
    for i, k in enumerate(keys):
        print(f"[{i}] {k}")
        print("   keywords:", ", ".join(idx[k][:12]))
        print()

if __name__ == "__main__":
    build_index()
