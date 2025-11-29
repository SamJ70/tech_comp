# backend/app/services/news_classifier.py
import re
from typing import Tuple, Dict, Any

# Simple keyword-driven classifier. Returns category and scores dict.
CATEGORIES = {
    "military": [
        "military", "weapon", "weaponization", "munition", "defense industry", "armed forces",
        "missile", "drone strike", "combat", "warfare", "militar", "munition", "soldier", "navy", "airforce"
    ],
    "policy": [
        "policy", "regulation", "regulator", "legislation", "law", "government policy",
        "minister", "parliament", "ban", "sanction", "export control", "guideline", "policy brief"
    ],
    "industry": [
        "launch", "startup", "company", "commercial", "industry", "investment", "funding",
        "acquisition", "contract", "supplier"
    ],
    "research": [
        "study", "research", "paper", "evidence", "journal", "university", "laboratory", "preprint",
        "conference", "doi", "arxiv", "crossref", "semantic scholar"
    ],
    "export_control": [
        "export control", "dual-use", "export licence", "export licence", "Wassenaar", "embargo",
        "export-control", "exportcontrol"
    ]
}

def _score_text_for_category(text: str, keywords) -> int:
    score = 0
    t = text.lower()
    for kw in keywords:
        # word boundary match and also phrase match
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            score += 2
        elif kw in t:
            score += 1
    return score

def classify_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: article dict with fields 'title', 'abstract' or 'description', optionally 'source' and 'url'.
    Returns: { category: str, scores: {...}, top_hit: str }.
    """
    text = " ".join([str(article.get(k, "")) for k in ("title", "abstract", "description", "content")])
    scores = {}
    for cat, kws in CATEGORIES.items():
        scores[cat] = _score_text_for_category(text, kws)
    # pick best non-zero
    best_cat = max(scores.items(), key=lambda x: x[1])
    category = best_cat[0] if best_cat[1] > 0 else "other"
    # also provide simple confidence (normalized)
    total = sum(scores.values()) or 1
    confidence = round(best_cat[1] / total, 3)
    return {"category": category, "scores": scores, "confidence": confidence}
