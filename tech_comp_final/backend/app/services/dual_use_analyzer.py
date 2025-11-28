# backend/app/services/dual_use_analyzer.py
import os
import json
import re
import logging
from typing import Dict, Any, List, Tuple
from rapidfuzz import process, fuzz
import pdfplumber

logger = logging.getLogger(__name__)

# semantic imports are optional (fallback to fuzzy only)
try:
    from sentence_transformers import SentenceTransformer, util
    EMB_MODEL = SentenceTransformer(os.getenv("VERIFIER_MODEL", "all-MiniLM-L6-v2"))
except Exception as e:
    EMB_MODEL = None
    logger.info("sentence-transformers not available; semantic matching disabled: %s", e)

from app.config import WASSENAAR_PDF, WASSENAAR_INDEX

# small stoplist
STOPWORDS = set([
    "equipment", "system", "systems", "technology", "technologies", "the", "and", "for", "of", "in", "with", "to",
    "a", "an", "by", "on", "from", "using"
])

def _tokenize_keywords(text: str, min_len: int = 4, topN: int = 8) -> List[str]:
    # simple keyword extractor: pick words longer than min_len, exclude stopwords, return top unique
    words = re.findall(r"[A-Za-z0-9\-]{4,}", text.lower())
    freqs = {}
    for w in words:
        if w in STOPWORDS: continue
        freqs[w] = freqs.get(w, 0) + 1
    sorted_keys = sorted(freqs.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in sorted_keys[:topN]]

class DualUseAnalyzer:
    def __init__(self, pdf_path: str = None, cache_json: str = None):
        self.pdf_path = pdf_path or WASSENAAR_PDF
        self.cache_json = cache_json or WASSENAAR_INDEX
        self.index = []
        self._choices = []
        self._choice_metadata = []

        if os.path.exists(self.cache_json):
            try:
                with open(self.cache_json, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
            except Exception:
                logger.exception("Failed to load existing Wassenaar index; will reparse.")
                self.index = []

        if not self.index and os.path.exists(self.pdf_path):
            self.index = self._parse_wassenaar_pdf(self.pdf_path)
            try:
                with open(self.cache_json, "w", encoding="utf-8") as f:
                    json.dump(self.index, f, ensure_ascii=False, indent=2)
            except Exception:
                logger.exception("Failed to write Wassenaar index cache")

        # flatten choices and metadata for fuzzy matching
        for it in self.index:
            text = it.get("text", "")
            self._choices.append(text)
            self._choice_metadata.append(it)

        # precompute embeddings for index entries (optional)
        if EMB_MODEL and self._choices:
            try:
                self._index_embeddings = EMB_MODEL.encode(self._choices, convert_to_tensor=True)
            except Exception as e:
                logger.exception("Failed to encode Wassenaar index embeddings: %s", e)
                self._index_embeddings = None
        else:
            self._index_embeddings = None

    def _parse_wassenaar_pdf(self, path: str) -> List[Dict[str, Any]]:
        """
        Heuristic PDF parsing:
        - extract text per page
        - build paragraphs by merging lines until blank lines
        - select paragraphs that look like list items (contain tech keywords or codes)
        - for each paragraph, extract candidate keywords
        """
        items: List[Dict[str, Any]] = []
        try:
            with pdfplumber.open(path) as pdf:
                pages_text = []
                for p in pdf.pages:
                    txt = p.extract_text() or ""
                    pages_text.append(txt)
            full = "\n\n".join(pages_text)
        except Exception as e:
            logger.exception("Failed to extract text from Wassenaar PDF: %s", e)
            return items

        # split into paragraphs on double newlines or lines starting with digit/letter code patterns
        paragraphs = re.split(r"\n\s*\n", full)
        # normalise and filter
        candidate_paragraphs = []
        kw_hint = ["equipment", "technology", "software", "material", "system", "component",
                   "processor", "sensor", "detector", "algorithm", "encryption", "biological", "gene"]
        for p in paragraphs:
            p_clean = " ".join([l.strip() for l in p.splitlines() if l.strip()])
            if len(p_clean) < 30:
                continue
            low = p_clean.lower()
            if any(k in low for k in kw_hint) or re.search(r"[0-9]\.[A-Z0-9]", p_clean) or len(p_clean) > 120:
                candidate_paragraphs.append(p_clean)

        # deduplicate
        seen = set()
        for p in candidate_paragraphs:
            if p in seen: continue
            seen.add(p)
            keywords = _tokenize_keywords(p, min_len=4, topN=10)
            items.append({"text": p, "keywords": keywords})

        # if nothing extracted, fallback to splitting by lines and taking longer lines
        if not items:
            lines = [l.strip() for l in full.splitlines() if len(l.strip()) > 40]
            for ln in lines[:800]:
                keywords = _tokenize_keywords(ln, min_len=4, topN=8)
                items.append({"text": ln, "keywords": keywords})

        logger.info("Wassenaar parse produced %d candidate items", len(items))
        return items

    def analyze_dual_use(self, country: str, domain: str, country_data: Dict[str, Any], time_range: int = None) -> Dict[str, Any]:
        """
        Multi-stage detection:
          1) exact keyword boost (if an item's keywords overlap Wassenaar keywords)
          2) fuzzy matching (RapidFuzz) with a moderate threshold
          3) semantic similarity (if embeddings available) with a moderate threshold
        Returns structured analysis with matched entries, confidence, recommendations.
        """
        # Build candidate texts from country_data
        candidates: List[str] = []
        for src in ("publications", "patents", "news", "tim", "aspi"):
            for it in country_data.get(src, []):
                t = (it.get("title") or "")[:1200]
                s = (it.get("abstract") or "")[:1500]
                if t:
                    candidates.append(t)
                if s:
                    candidates.append(s)

        # dedupe and limit
        candidates = list(dict.fromkeys(candidates))[:800]

        matched: List[Dict[str, Any]] = []

        # Precompute candidate embeddings if EMB_MODEL present
        candidate_embeddings = None
        if EMB_MODEL and candidates:
            try:
                candidate_embeddings = EMB_MODEL.encode(candidates, convert_to_tensor=True)
            except Exception as e:
                logger.info("Failed to compute candidate embeddings: %s", e)
                candidate_embeddings = None

        # Domain keyword boosters (help with domain-specific mapping)
        domain_boost_keywords = {
            "Artificial Intelligence": ["machine learning", "deep learning", "neural network", "transformer", "nlp", "computer vision", "gan", "reinforcement"],
            "Biotechnology": ["gene", "viral", "bioreactor", "CRISPR", "cell", "biological", "pathogen"],
            "Space Technology": ["satellite", "rocket", "launcher", "satcom", "orbiter", "payload"],
            "Quantum Computing": ["qubit", "quantum", "superposition", "entanglement", "photon"],
            "Robotics": ["robot", "actuator", "autonomous", "manipulator", "uav", "drone"],
            "Cybersecurity": ["encryption", "cryptography", "exploit", "vulnerability", "malware", "backdoor"]
        }
        boosters = domain_boost_keywords.get(domain, [])

        # Step A: keyword overlaps (fast)
        for idx, cand in enumerate(candidates[:500]):
            cand_low = cand.lower()
            best = None
            # exact keyword overlap with Wassenaar keywords
            for i, meta in enumerate(self._choice_metadata):
                kws = meta.get("keywords", [])
                if not kws: continue
                overlap = sum(1 for k in kws if k in cand_low)
                if overlap >= 1:
                    # initial fuzzy match to rank
                    score = fuzz.token_set_ratio(cand_low, meta.get("text",""))
                    if score >= 55:
                        best = {"candidate_index": idx, "choice_index": i, "score": int(score), "method": "keyword_overlap"}
                        matched.append({
                            "token": cand[:400],
                            "matched_text": meta.get("text","")[:1000],
                            "score": int(score),
                            "method": "keyword_overlap"
                        })

        # Step B: fuzzy matching (RapidFuzz) on remaining candidates
        for cand in candidates[:400]:
            if not self._choices:
                break
            match, score, idx = process.extractOne(cand, self._choices, scorer=fuzz.token_sort_ratio) or (None, 0, None)
            # boost if domain words present
            boost = 0
            for b in boosters:
                if b in cand.lower():
                    boost += 7
            final_score = score + boost
            if match and final_score >= 65:
                meta = self._choice_metadata[idx]
                matched.append({"token": cand[:400], "matched_text": match, "score": int(final_score), "method": "fuzzy", "meta": meta})

        # Step C: semantic similarity if embeddings available
        if EMB_MODEL and self._index_embeddings is not None and candidate_embeddings is not None:
            try:
                cos = util.cos_sim(candidate_embeddings, self._index_embeddings)
                # cos is matrix candidates x index
                import torch
                cos_np = cos.cpu().numpy()
                for i in range(cos_np.shape[0]):
                    best_idx = int(cos_np[i].argmax())
                    best_score = float(cos_np[i, best_idx])
                    if best_score >= 0.55:  # semantic threshold (0..1)
                        meta = self._choice_metadata[best_idx]
                        matched.append({
                            "token": candidates[i][:400],
                            "matched_text": meta.get("text","")[:1000],
                            "score": int(best_score * 100),
                            "method": "semantic",
                            "meta": meta
                        })
            except Exception as e:
                logger.exception("Semantic matching pass failed: %s", e)

        # Normalize matched (dedupe by matched_text)
        dedup = {}
        for m in matched:
            key = m.get("matched_text")[:200]
            prev = dedup.get(key)
            if not prev or m.get("score",0) > prev.get("score",0):
                dedup[key] = m
        matched_list = sorted(dedup.values(), key=lambda x: x.get("score",0), reverse=True)

        # Heuristic severity
        severity = "LOW"
        if any(m["score"] >= 92 for m in matched_list):
            severity = "CRITICAL"
        elif any(m["score"] >= 85 for m in matched_list):
            severity = "HIGH"
        elif any(m["score"] >= 70 for m in matched_list):
            severity = "MODERATE"

        safe_limit = "restricted" if severity in ("HIGH", "CRITICAL") else "permitted"

        # build output
        out = {
            "risk_level": severity,
            "risk_description": f"Heuristic matched {len(matched_list)} potential Wassenaar-relevant entries (multi-stage matching).",
            "compliance_status": "NON_COMPLIANT" if severity in ("HIGH","CRITICAL") else ("MONITORING_REQUIRED" if severity=="MODERATE" else "COMPLIANT"),
            "compliance_notes": f"Top matches: {', '.join([m['matched_text'][:120] for m in matched_list[:6]])}",
            "wassenaar_category": matched_list[0]["matched_text"] if matched_list else "Not matched",
            "safe_limit": safe_limit,
            "military_indicators": matched_list[:200],
            "recommendations": self._recommendations_for_severity(severity),
            "confidence_score": min(0.99, sum([m.get("score",0) for m in matched_list[:5]]) / 500.0 if matched_list else 0.05
                                 )
        }
        return out

    def _recommendations_for_severity(self, severity: str) -> List[str]:
        recs = []
        if severity in ("HIGH","CRITICAL"):
            recs.append("Immediate internal review and export-control check recommended.")
            recs.append("Contact national export control authority for classification.")
            recs.append("Temporarily restrict external dissemination of flagged projects.")
        elif severity == "MODERATE":
            recs.append("Flag similar future outputs for human review.")
            recs.append("Monitor collaborations and external beneficiaries.")
        else:
            recs.append("No immediate dual-use flag detected; maintain routine monitoring.")
        return recs
