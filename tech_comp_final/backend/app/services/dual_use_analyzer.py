# backend/app/services/dual_use_analyzer.py
import os
import math
import logging
from typing import Dict, Any, List
from collections import defaultdict, Counter
from app.services.wassenaar_parser import parse_wassenaar
from app.config import REPORTS_DIR
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except Exception:
    RAPIDFUZZ_AVAILABLE = False

logger = logging.getLogger(__name__)

# Add curated additional categories (beyond Wassenaar) to increase coverage
CURATED_CATEGORIES = {
    "autonomous_systems": ["autonomous", "autonomy", "autonomous vehicle", "autonomous system"],
    "surveillance_and_imaging": ["surveillance", "facial recognition", "object detection", "imaging system", "camera"],
    "cyber_weapons_and_intrusion": ["malware", "exploit", "ransomware", "rootkit", "ddos", "cyber attack"],
    "precision_guidance": ["guidance", "targeting", "precision-guided", "seeker", "avionics"],
    "missile_and_rocketry": ["rocket", "propellant", "warhead", "missile", "booster"],
    "materials_and_manufacturing": ["additive manufacturing", "3d printing", "composite", "metal powder"],
    "quantum_technologies": ["quantum", "qubit", "quantum computing", "quantum sensor"],
    "communications": ["satcom", "jammer", "encrypted communication", "modem", "radio"]
}

# Severity thresholds (fuzzy score or direct hits)
SEVERITY_WEIGHTS = {
    "exact": 3.0,     # exact keyword present
    "fuzzy_high": 2.0,
    "fuzzy_med": 1.0,
    "fuzzy_low": 0.5
}

def _fuzzy_score(text: str, keyword: str) -> float:
    if not text or not keyword:
        return 0.0
    t = text.lower()
    k = keyword.lower()
    if k in t:
        return SEVERITY_WEIGHTS["exact"]
    if not RAPIDFUZZ_AVAILABLE:
        # fallback basic partial matching
        return SEVERITY_WEIGHTS["fuzzy_low"] if k[:5] in t else 0.0
    score = fuzz.partial_ratio(k, t)
    if score >= 95:
        return SEVERITY_WEIGHTS["fuzzy_high"]
    if score >= 80:
        return SEVERITY_WEIGHTS["fuzzy_med"]
    if score >= 60:
        return SEVERITY_WEIGHTS["fuzzy_low"]
    return 0.0

class DualUseAnalyzer:
    def __init__(self, extra_keywords: Dict[str, List[str]] = None):
        self.wassenaar = parse_wassenaar()
        # merge curated categories into a combined category map
        self.category_map = {}
        # normalized names
        for k, v in self.wassenaar.items():
            # use only last path element for short name
            short = k.replace(" ", "_").lower()
            self.category_map[short] = v
        for k, v in CURATED_CATEGORIES.items():
            if k in self.category_map:
                self.category_map[k].extend(v)
            else:
                self.category_map[k] = list(set(v))
        if extra_keywords:
            for k, v in extra_keywords.items():
                self.category_map.setdefault(k, []).extend(v)

    def analyze_dual_use(self, country: str, domain: str, country_data: Dict[str, Any], years_back=None) -> Dict[str, Any]:
        """
        Analyze country_data (contains 'publications','news','tim','aspi', etc.) and return:
        {
           risk_level, risk_score (0-100), compliance_status, compliance_notes,
           category_breakdown: {category: {score, matches:[{text,score,source}]}}
        }
        """
        combined_texts = []
        # we will scan titles, abstracts, descriptions for matches
        for src in ("publications", "news", "tim", "aspi", "patents"):
            for it in country_data.get(src, []):
                text = (it.get("title") or "") + " " + (it.get("abstract") or "") + " " + (it.get("description") or "") 
                combined_texts.append({"text": text, "source": src, "item": it})

        # category scoring
        category_scores = defaultdict(float)
        category_matches = defaultdict(list)
        total_matches = 0
        for entry in combined_texts:
            txt = entry["text"]
            src = entry["source"]
            for cat, keywords in self.category_map.items():
                # iterate keywords and compute fuzzy scores; keep top match for entry-cat
                best_score = 0.0
                best_kw = None
                for kw in keywords:
                    s = _fuzzy_score(txt, kw)
                    if s > best_score:
                        best_score = s
                        best_kw = kw
                if best_score > 0:
                    # accumulate weighted score
                    category_scores[cat] += best_score
                    total_matches += 1
                    # record match sample
                    category_matches[cat].append({
                        "matched_keyword": best_kw,
                        "score": best_score,
                        "source": src,
                        "title": (entry["item"].get("title") or "")[:300],
                        "year": entry["item"].get("year") or entry["item"].get("publishedAt")
                    })

        # Normalize and produce severity
        # risk_score: weighted function of highest categories + breadth
        cat_counts = {c: len(v) for c, v in category_matches.items()}
        top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:8]
        breadth = len(cat_counts)
        raw_strength = sum(category_scores.values())

        # compute normalized score 0-100
        # base on raw_strength, breadth, and presence of high-risk categories
        score = min(100, int((raw_strength * 10) + (breadth * 5)))

        # bump risk if keywords in explicitly military categories appear (heuristic)
        military_like = ["missile", "rocket", "warhead", "precision_guidance", "autonomous_systems", "surveillance_and_imaging", "cyber_weapons_and_intrusion"]
        military_score = 0.0
        for m in military_like:
            military_score += category_scores.get(m, 0.0)
        if military_score > 6:
            score = min(100, score + 15)
        elif military_score > 2:
            score = min(100, score + 7)

        # risk_level thresholds
        if score >= 70:
            risk_level = "CRITICAL"
        elif score >= 45:
            risk_level = "HIGH"
        elif score >= 20:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # compliance status heuristics
        # if critical & many matches -> non-compliant
        if risk_level in ("CRITICAL", "HIGH") and total_matches > 8:
            compliance = "MONITORING_REQUIRED"
            compliance_notes = "Multiple high-confidence matches to dual-use categories detected; consider deeper manual review and export-control checks (Wassenaar keywords matched)."
        elif risk_level == "CRITICAL":
            compliance = "CRITICAL_VIOLATION"
            compliance_notes = "Critical risk detected — high concentration of potentially military-relevant technologies."
        else:
            compliance = "COMPLIANT"
            compliance_notes = "No immediate export-control concerns found by automated heuristics; continue monitoring."

        # top matched per category (top 5)
        compact_matches = {}
        for c, matches in category_matches.items():
            sorted_m = sorted(matches, key=lambda x: x["score"], reverse=True)[:8]
            compact_matches[c] = sorted_m

        # recommendations (rule-based)
        recs = []
        if risk_level in ("HIGH", "CRITICAL"):
            recs.append("Initiate manual document review of all items flagged in 'Top Matches' (priority by score).")
            recs.append("Check for export licenses and Wassenaar categories for matched items.")
            recs.append("Cross-check authors/affiliations for military/employer ties and assess controlled technology transfer risks.")
            recs.append("Increase monitoring frequency for this domain and country to weekly.")
        elif risk_level == "MODERATE":
            recs.append("Monitor developments and collect additional provenance for top-matched items.")
            recs.append("Flag suspicious items for analyst review; no immediate escalation required.")
        else:
            recs.append("Continue periodic monitoring; no immediate export-control action recommended.")

        return {
            "risk_level": risk_level,
            "risk_score": score,
            "compliance_status": compliance,
            "compliance_notes": compliance_notes,
            "category_breakdown": {
                "scores": {c: round(s, 2) for c, s in category_scores.items()},
                "counts": cat_counts,
                "top_matches": compact_matches
            },
            "recommendations": recs,
            "total_matches": total_matches
        }
