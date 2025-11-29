# backend/app/services/wassenaar_parser.py
import os
import json
import logging
from typing import Dict, List
from app.config import WASSENAAR_PDF, WASSENAAR_INDEX, DATA_DIR

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)

def _simple_split_lines(text: str) -> List[str]:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s: 
            continue
        # skip very short garbage
        if len(s) < 3:
            continue
        lines.append(s)
    return lines

def parse_wassenaar(pdf_path: str = None, cache_path: str = None) -> Dict[str, List[str]]:
    """
    Parse Wassenaar PDF into category->keywords mapping. Cached to WASSENAAR_INDEX.
    Returns a dictionary {category_name: [keywords...]}
    """
    pdf_path = pdf_path or WASSENAAR_PDF
    cache_path = cache_path or WASSENAAR_INDEX

    # if cached, return cached
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.info("Failed to load existing cache, will reparse.")

    # fallback simple map if pdfplumber not available
    if not PDFPLUMBER_AVAILABLE:
        logger.warning("pdfplumber not available. Returning fallback categories.")
        fallback = {
            "ai_algorithms": ["machine learning", "neural network", "deep learning", "ai model", "training dataset"],
            "biotech": ["bioreactor", "cell culture", "gene editing", "crispr"],
            "radar_and_sensors": ["radar", "lidar", "sonar", "sensor", "imaging"],
            "navigation": ["gnss", "gps", "inertial", "navigation"],
            "uav_and_aircraft": ["drone", "uav", "unmanned", "airframe"],
        }
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(fallback, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return fallback

    # parse PDF heuristically
    try:
        text_accum = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                text_accum.append(p.extract_text() or "")
        full_text = "\n".join(text_accum)
        lines = _simple_split_lines(full_text)

        categories = {}
        current_cat = "general"
        buffer = []
        for line in lines:
            is_heading = False
            # heuristics for headings
            if line.isupper() or line.endswith(":") or "ANNEX" in line.upper() or "CATEGORY" in line.upper():
                is_heading = True
            if is_heading:
                # commit previous buffer
                if buffer:
                    kws = set()
                    for b in buffer:
                        # take tokens
                        for token in b.replace(",", " ").split():
                            token = token.strip().lower()
                            if len(token) > 3:
                                kws.add(token)
                    categories[current_cat] = sorted(list(kws))
                current_cat = line.strip().rstrip(":—").lower()
                buffer = []
            else:
                buffer.append(line)
        # final commit
        if buffer:
            kws = set()
            for b in buffer:
                for token in b.replace(",", " ").split():
                    token = token.strip().lower()
                    if len(token) > 3:
                        kws.add(token)
            categories[current_cat] = sorted(list(kws))

        # keep only categories with keywords
        categories = {k: v for k, v in categories.items() if v}
        if not categories:
            raise ValueError("No categories extracted from Wassenaar PDF")

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)

        return categories

    except Exception as e:
        logger.exception("Failed parsing Wassenaar PDF: %s", e)
        # fallback tiny map
        fallback = {
            "ai_algorithms": ["machine learning", "neural network", "deep learning", "ai model", "training dataset"],
            "biotech": ["bioreactor", "cell culture", "gene editing", "crispr"],
            "radar_and_sensors": ["radar", "lidar", "sonar", "sensor", "imaging"],
        }
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(fallback, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return fallback
