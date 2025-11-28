# backend/app/services/fact_verifier.py
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict
import numpy as np
from ..config import VERIFIER_MODEL
import logging

logger = logging.getLogger(__name__)

class FactVerifier:
    def __init__(self, model_name: str = VERIFIER_MODEL):
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            logger.exception("Failed to load embedding model: %s", e)
            self.model = None

    def score_claim_against_evidence(self, claim: str, evidence_snippets: List[str]) -> Dict:
        if not self.model:
            return {"score": 0.0, "ranked_evidence": []}
        claim_emb = self.model.encode(claim, convert_to_tensor=True)
        ev_emb = self.model.encode(evidence_snippets, convert_to_tensor=True)
        sims = util.cos_sim(claim_emb, ev_emb)[0].cpu().numpy().tolist()
        ranked = sorted(zip(evidence_snippets, sims), key=lambda x: x[1], reverse=True)
        score = float(np.max(sims) if sims else 0.0)
        return {
            "score": score,
            "ranked_evidence": [{"snippet": r[0], "similarity": float(r[1])} for r in ranked[:10]]
        }
