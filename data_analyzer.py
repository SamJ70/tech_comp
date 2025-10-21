from typing import Dict, List
import re
from collections import Counter

class DataAnalyzer:
    def __init__(self):
        self.tech_keywords = {
            "research": ["research", "development", "innovation", "scientific", "study", "investigation"],
            "industry": ["startup", "company", "corporation", "industry", "commercial", "enterprise"],
            "government": ["government", "policy", "initiative", "national", "ministry", "program"],
            "investment": ["investment", "funding", "capital", "venture", "finance", "billion"],
            "education": ["university", "institute", "education", "training", "academic", "scholar"],
            "innovation": ["patent", "innovation", "breakthrough", "advancement", "cutting-edge"]
        }
    
    def analyze_and_compare(
        self, 
        country1: str, 
        country2: str, 
        domain: str,
        country1_data: Dict,
        country2_data: Dict
    ) -> Dict:
        country1_analysis = self._analyze_country_data(country1, domain, country1_data)
        country2_analysis = self._analyze_country_data(country2, domain, country2_data)
        
        comparison = self._generate_comparison(
            country1, country2, country1_analysis, country2_analysis
        )
        
        overall_analysis = self._generate_overall_analysis(
            country1, country2, domain, comparison
        )
        
        return {
            "summary": {
                country1: country1_analysis["summary"],
                country2: country2_analysis["summary"]
            },
            "comparison": comparison,
            "overall_analysis": overall_analysis,
            "resources": {
                country1: country1_analysis["key_entities"],
                country2: country2_analysis["key_entities"]
            },
            "news": country1_analysis["highlights"] + country2_analysis["highlights"]
        }
    
    def _analyze_country_data(self, country: str, domain: str, data: Dict) -> Dict:
        combined_text = " ".join(data.get("raw_text", []))
        
        if not combined_text or len(combined_text) < 100:
            combined_text = f"{country} is developing its {domain} sector through various initiatives and investments."
        
        keyword_scores = {}
        for category, keywords in self.tech_keywords.items():
            score = sum(combined_text.lower().count(kw) for kw in keywords)
            keyword_scores[category] = score
        
        summary = self._generate_summary(country, domain, combined_text, keyword_scores)
        
        key_entities = self._extract_key_entities(combined_text, country)
        
        highlights = self._extract_highlights(combined_text, domain)
        
        return {
            "summary": summary,
            "keyword_scores": keyword_scores,
            "key_entities": key_entities,
            "highlights": highlights,
            "text_length": len(combined_text)
        }
    
    def _generate_summary(self, country: str, domain: str, text: str, scores: Dict) -> str:
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 50][:15]
        
        relevant_sentences = []
        for sentence in sentences:
            if country.lower() in sentence.lower() and domain.lower() in sentence.lower():
                relevant_sentences.append(sentence)
        
        if len(relevant_sentences) >= 2:
            summary = ". ".join(relevant_sentences[:2]) + "."
        elif len(relevant_sentences) == 1:
            summary = relevant_sentences[0] + "."
        else:
            if scores:
                top_category = max(scores.items(), key=lambda x: x[1])[0]
            else:
                top_category = "development"
            summary = f"{country} is actively involved in {domain} with significant focus on {top_category} and technological advancement."
        
        return summary[:500]
    
    def _extract_key_entities(self, text: str, country: str) -> List[str]:
        entities = []
        
        capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        matches = re.findall(capitalized_pattern, text)
        
        entity_counts = Counter(matches)
        
        entities = [entity for entity, count in entity_counts.most_common(8) 
                   if entity != country and len(entity.split()) <= 4]
        
        return entities[:6]
    
    def _extract_highlights(self, text: str, domain: str) -> List[Dict]:
        sentences = re.split(r'[.!?]+', text)
        highlights = []
        
        keywords = ["announced", "launched", "developed", "breakthrough", "innovation", "investment"]
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords) and domain.lower() in sentence.lower():
                highlights.append({
                    "source": "Research Article",
                    "headline": sentence.strip()[:150] + "..."
                })
                if len(highlights) >= 2:
                    break
        
        return highlights
    
    def _generate_comparison(
        self, 
        country1: str, 
        country2: str, 
        analysis1: Dict, 
        analysis2: Dict
    ) -> Dict:
        comparison = {}
        
        for category in self.tech_keywords.keys():
            score1 = analysis1["keyword_scores"].get(category, 0)
            score2 = analysis2["keyword_scores"].get(category, 0)
            
            if score1 > score2 * 1.5:
                comparison[f"{category}_activity"] = f"{country1} shows significantly higher activity (score: {score1} vs {score2})"
            elif score2 > score1 * 1.5:
                comparison[f"{category}_activity"] = f"{country2} shows significantly higher activity (score: {score2} vs {score1})"
            elif score1 > score2:
                comparison[f"{category}_activity"] = f"{country1} leads slightly (score: {score1} vs {score2})"
            elif score2 > score1:
                comparison[f"{category}_activity"] = f"{country2} leads slightly (score: {score2} vs {score1})"
            else:
                comparison[f"{category}_activity"] = f"Both countries show similar levels (score: {score1} vs {score2})"
        
        return comparison
    
    def _generate_overall_analysis(
        self, 
        country1: str, 
        country2: str, 
        domain: str, 
        comparison: Dict
    ) -> str:
        leads = {country1: 0, country2: 0}
        
        for key, value in comparison.items():
            if country1 in value and ("significantly higher" in value or "leads" in value):
                leads[country1] += 1
            elif country2 in value and ("significantly higher" in value or "leads" in value):
                leads[country2] += 1
        
        if leads[country1] > leads[country2]:
            leader = country1
            follower = country2
        elif leads[country2] > leads[country1]:
            leader = country2
            follower = country1
        else:
            return f"Both {country1} and {country2} demonstrate balanced capabilities in {domain}, with each country showing strengths in different areas of technological development and implementation."
        
        analysis = f"{leader} currently demonstrates a stronger position in {domain} compared to {follower}, "
        analysis += f"with particular advantages in research activity, government initiatives, and industry development. "
        analysis += f"However, {follower} is actively developing its {domain} sector and shows potential for growth "
        analysis += f"through strategic investments and policy initiatives."
        
        return analysis
