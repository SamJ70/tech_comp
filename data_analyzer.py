from typing import Dict, List, Tuple
import re
from collections import Counter
from datetime import datetime

class DataAnalyzer:
    def __init__(self):
        self.tech_keywords = {
            "research": ["research", "development", "innovation", "scientific", "study", "investigation", "laboratory", "paper"],
            "industry": ["startup", "company", "corporation", "industry", "commercial", "enterprise", "firm", "tech giant"],
            "government": ["government", "policy", "initiative", "national", "ministry", "program", "regulation", "strategy"],
            "investment": ["investment", "funding", "capital", "venture", "finance", "billion", "million", "valuation"],
            "education": ["university", "institute", "education", "training", "academic", "scholar", "graduate"],
            "innovation": ["patent", "innovation", "breakthrough", "advancement", "cutting-edge", "pioneering"]
        }
        
        self.current_year = datetime.now().year
    
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
            country1, country2, domain, country1_analysis, country2_analysis
        )
        
        overall_analysis = self._generate_overall_analysis(
            country1, country2, domain, country1_analysis, country2_analysis, comparison
        )
        
        return {
            "summary": {
                country1: country1_analysis["summary"],
                country2: country2_analysis["summary"]
            },
            "comparison": comparison,
            "overall_analysis": overall_analysis,
            "metrics": {
                country1: country1_analysis["metrics"],
                country2: country2_analysis["metrics"]
            },
            "resources": {
                country1: country1_analysis["key_entities"],
                country2: country2_analysis["key_entities"]
            },
            "news": country1_analysis["highlights"] + country2_analysis["highlights"]
        }
    
    def _analyze_country_data(self, country: str, domain: str, data: Dict) -> Dict:
        combined_text = " ".join(data.get("raw_text", []))
        text_length = len(combined_text)
        
        if text_length < 100:
            combined_text = f"{country} is developing its {domain} sector through various initiatives and investments."
            text_length = len(combined_text)
        
        normalized_keyword_scores = self._calculate_normalized_scores(combined_text, text_length)
        
        numerical_data = self._extract_numerical_data(combined_text, domain)
        
        companies = self._extract_companies(combined_text, domain)
        
        recent_developments = self._extract_recent_developments(combined_text, domain, country)
        
        summary = self._generate_summary(country, domain, combined_text, recent_developments)
        
        key_entities = self._extract_key_entities(combined_text, country)
        
        highlights = self._extract_highlights(combined_text, domain, country)
        
        metrics = {
            "total_companies_mentioned": len(companies),
            "funding_amounts": numerical_data["funding"],
            "recent_developments_count": len(recent_developments),
            "normalized_activity_score": sum(normalized_keyword_scores.values()) / len(normalized_keyword_scores) if normalized_keyword_scores else 0,
            "text_coverage": text_length
        }
        
        return {
            "summary": summary,
            "normalized_scores": normalized_keyword_scores,
            "metrics": metrics,
            "companies": companies[:10],
            "recent_developments": recent_developments[:5],
            "numerical_data": numerical_data,
            "key_entities": key_entities,
            "highlights": highlights,
            "text_length": text_length
        }
    
    def _calculate_normalized_scores(self, text: str, text_length: int) -> Dict[str, float]:
        """Calculate keyword scores normalized per 10,000 characters"""
        normalized_scores = {}
        text_lower = text.lower()
        
        for category, keywords in self.tech_keywords.items():
            raw_count = sum(text_lower.count(kw) for kw in keywords)
            normalized_score = (raw_count / text_length) * 10000 if text_length > 0 else 0
            normalized_scores[category] = round(normalized_score, 2)
        
        return normalized_scores
    
    def _extract_numerical_data(self, text: str, domain: str) -> Dict:
        """Extract numerical facts like funding amounts, company counts, etc."""
        data = {
            "funding": [],
            "valuations": [],
            "market_size": [],
            "growth_rate": []
        }
        
        billion_pattern = r'(\$?\d+(?:\.\d+)?)\s*billion'
        billion_matches = re.findall(billion_pattern, text, re.IGNORECASE)
        data["funding"].extend([f"${m} billion" for m in billion_matches[:5]])
        
        million_pattern = r'(\$?\d+(?:\.\d+)?)\s*million'
        million_matches = re.findall(million_pattern, text, re.IGNORECASE)
        data["funding"].extend([f"${m} million" for m in million_matches[:3]])
        
        growth_pattern = r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:growth|increase)'
        growth_matches = re.findall(growth_pattern, text, re.IGNORECASE)
        data["growth_rate"].extend([f"{m}%" for m in growth_matches[:3]])
        
        return data
    
    def _extract_companies(self, text: str, domain: str) -> List[str]:
        """Extract company and organization names"""
        companies = []
        
        company_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Technologies|Labs|Systems|Solutions|AI|Tech)))\b',
            r'\b(Google|Microsoft|Amazon|Apple|Meta|Facebook|IBM|Intel|NVIDIA|OpenAI|DeepMind|Tesla)\b',
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        company_counts = Counter(companies)
        unique_companies = [comp for comp, count in company_counts.most_common(15)]
        
        return unique_companies
    
    def _extract_recent_developments(self, text: str, domain: str, country: str) -> List[Dict]:
        """Extract developments from recent years (2020-2025)"""
        developments = []
        sentences = re.split(r'[.!?]+', text)
        
        recent_years = [str(year) for year in range(2020, self.current_year + 2)]
        
        development_keywords = [
            "launched", "announced", "developed", "released", "introduced",
            "breakthrough", "innovation", "established", "created", "unveiled",
            "invested", "acquired", "partnership", "collaboration"
        ]
        
        for sentence in sentences:
            has_recent_year = any(year in sentence for year in recent_years)
            has_development_keyword = any(kw in sentence.lower() for kw in development_keywords)
            is_relevant = domain.lower() in sentence.lower() or any(tech_kw in sentence.lower() for tech_kw in ['ai', 'artificial', 'technology', 'innovation'])
            
            if has_recent_year and has_development_keyword and is_relevant and len(sentence.strip()) > 40:
                year_match = re.search(r'(20\d{2})', sentence)
                year = year_match.group(1) if year_match else "Recent"
                
                developments.append({
                    "year": year,
                    "description": sentence.strip()[:200]
                })
                
                if len(developments) >= 10:
                    break
        
        developments.sort(key=lambda x: x["year"], reverse=True)
        return developments
    
    def _generate_summary(self, country: str, domain: str, text: str, recent_developments: List[Dict]) -> str:
        """Generate country summary focusing on recent achievements"""
        if recent_developments:
            latest_dev = recent_developments[0]["description"][:300]
            summary = f"{country}'s {domain} sector: {latest_dev}"
        else:
            sentences = re.split(r'[.!?]+', text)
            relevant_sentences = []
            
            for sentence in sentences[:100]:
                if country.lower() in sentence.lower() and domain.lower() in sentence.lower():
                    if len(sentence.strip()) > 50:
                        relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                summary = relevant_sentences[0][:400]
            else:
                summary = f"{country} is actively developing its {domain} capabilities through various initiatives and technological advancements."
        
        return summary[:500]
    
    def _extract_key_entities(self, text: str, country: str) -> List[str]:
        """Extract key organizations, institutions, and entities"""
        entities = []
        
        capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b'
        matches = re.findall(capitalized_pattern, text)
        
        entity_counts = Counter(matches)
        
        common_words = {'United States', 'New York', 'Retrieved', 'Press', 'The Times', 
                       'Retrieved July', 'Retrieved August', 'Retrieved March', 'Press Information'}
        
        entities = [entity for entity, count in entity_counts.most_common(20) 
                   if entity != country and len(entity.split()) <= 4 
                   and entity not in common_words
                   and count >= 2]
        
        return entities[:8]
    
    def _extract_highlights(self, text: str, domain: str, country: str) -> List[Dict]:
        """Extract recent news and highlights"""
        sentences = re.split(r'[.!?]+', text)
        highlights = []
        
        keywords = ["announced", "launched", "developed", "breakthrough", "innovation", 
                   "investment", "partnership", "acquired", "released", "unveiled"]
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                is_relevant = domain.lower() in sentence.lower() or country.lower() in sentence.lower()
                has_year = bool(re.search(r'20\d{2}', sentence))
                
                if is_relevant and len(sentence.strip()) > 50:
                    highlights.append({
                        "source": "Research Data",
                        "headline": sentence.strip()[:180] + "...",
                        "recent": has_year
                    })
                    
                    if len(highlights) >= 5:
                        break
        
        highlights.sort(key=lambda x: x.get("recent", False), reverse=True)
        return highlights
    
    def _generate_comparison(
        self, 
        country1: str, 
        country2: str, 
        domain: str,
        analysis1: Dict, 
        analysis2: Dict
    ) -> Dict:
        """Generate fair comparison using normalized metrics"""
        comparison = {}
        
        for category in self.tech_keywords.keys():
            score1 = analysis1["normalized_scores"].get(category, 0)
            score2 = analysis2["normalized_scores"].get(category, 0)
            
            diff_percent = abs(score1 - score2) / max(score1, score2, 1) * 100
            
            if diff_percent > 30:
                if score1 > score2:
                    comparison[f"{category}_activity"] = f"{country1} shows stronger {category} focus (normalized score: {score1} vs {score2})"
                else:
                    comparison[f"{category}_activity"] = f"{country2} shows stronger {category} focus (normalized score: {score2} vs {score1})"
            elif diff_percent > 10:
                if score1 > score2:
                    comparison[f"{category}_activity"] = f"{country1} leads slightly in {category} (score: {score1} vs {score2})"
                else:
                    comparison[f"{category}_activity"] = f"{country2} leads slightly in {category} (score: {score2} vs {score1})"
            else:
                comparison[f"{category}_activity"] = f"Similar {category} activity levels (score: {score1} vs {score2})"
        
        companies1 = len(analysis1.get("companies", []))
        companies2 = len(analysis2.get("companies", []))
        comparison["companies_mentioned"] = f"{country1}: {companies1} organizations | {country2}: {companies2} organizations"
        
        dev1 = len(analysis1.get("recent_developments", []))
        dev2 = len(analysis2.get("recent_developments", []))
        comparison["recent_developments"] = f"{country1}: {dev1} recent initiatives | {country2}: {dev2} recent initiatives"
        
        return comparison
    
    def _generate_overall_analysis(
        self, 
        country1: str, 
        country2: str, 
        domain: str,
        analysis1: Dict,
        analysis2: Dict,
        comparison: Dict
    ) -> str:
        """Generate balanced overall analysis based on evidence"""
        
        funding1 = analysis1.get("numerical_data", {}).get("funding", [])
        funding2 = analysis2.get("numerical_data", {}).get("funding", [])
        
        max_funding1 = self._extract_max_funding(funding1)
        max_funding2 = self._extract_max_funding(funding2)
        
        companies1 = analysis1.get("companies", [])
        companies2 = analysis2.get("companies", [])
        
        major_tech_companies = {
            'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta', 'Facebook', 
            'IBM', 'Intel', 'NVIDIA', 'OpenAI', 'DeepMind', 'Tesla', 'Anthropic'
        }
        
        major_companies1 = [c for c in companies1 if any(mc in c for mc in major_tech_companies)]
        major_companies2 = [c for c in companies2 if any(mc in c for mc in major_tech_companies)]
        
        dev1 = len(analysis1.get("recent_developments", []))
        dev2 = len(analysis2.get("recent_developments", []))
        
        evidence_points = {country1: [], country2: []}
        
        if max_funding1 and max_funding2:
            if max_funding1 > max_funding2 * 2:
                evidence_points[country1].append(f"significantly higher funding levels (up to {self._format_funding(max_funding1)} vs {self._format_funding(max_funding2)})")
            elif max_funding2 > max_funding1 * 2:
                evidence_points[country2].append(f"significantly higher funding levels (up to {self._format_funding(max_funding2)} vs {self._format_funding(max_funding1)})")
        
        if len(major_companies1) > len(major_companies2) * 1.5:
            evidence_points[country1].append(f"more global tech leaders ({len(major_companies1)} vs {len(major_companies2)})")
        elif len(major_companies2) > len(major_companies1) * 1.5:
            evidence_points[country2].append(f"more global tech leaders ({len(major_companies2)} vs {len(major_companies1)})")
        
        if dev1 > dev2 * 1.3:
            evidence_points[country1].append(f"more documented recent developments ({dev1} vs {dev2})")
        elif dev2 > dev1 * 1.3:
            evidence_points[country2].append(f"more documented recent developments ({dev2} vs {dev1})")
        
        total_points1 = len(evidence_points[country1])
        total_points2 = len(evidence_points[country2])
        
        if total_points1 > total_points2:
            leader = country1
            follower = country2
            leader_evidence = evidence_points[country1]
        elif total_points2 > total_points1:
            leader = country2
            follower = country1
            leader_evidence = evidence_points[country2]
        else:
            return (f"Both {country1} and {country2} show strong capabilities in {domain}. "
                   f"{country1} features {len(major_companies1)} major tech organizations and {dev1} recent developments, "
                   f"while {country2} has {len(major_companies2)} major tech organizations and {dev2} recent developments. "
                   f"Each country demonstrates distinct strengths across different dimensions of {domain} development.")
        
        evidence_str = ", ".join(leader_evidence) if leader_evidence else "multiple factors"
        
        analysis = (f"Based on analysis of documented evidence, {leader} demonstrates stronger indicators "
                   f"in {domain}, particularly in {evidence_str}. "
                   f"{leader} benefits from {', '.join(major_companies2 if leader == country2 else major_companies1) if (major_companies2 if leader == country2 else major_companies1) else 'significant industry presence'}. "
                   f"\n\n{follower} continues developing its {domain} capabilities through government initiatives and growing industry participation. "
                   f"Note: This analysis is based on publicly available Wikipedia data and represents documented information rather than comprehensive capability assessment.")
        
        return analysis
    
    def _extract_max_funding(self, funding_list: List[str]) -> float:
        """Extract maximum funding amount in billions"""
        max_funding = 0.0
        for item in funding_list:
            try:
                value_str = item.replace('$', '').replace(',', '').strip()
                if 'billion' in value_str.lower():
                    value = float(value_str.split()[0])
                    max_funding = max(max_funding, value)
                elif 'million' in value_str.lower():
                    value = float(value_str.split()[0]) / 1000
                    max_funding = max(max_funding, value)
            except (ValueError, IndexError):
                continue
        return max_funding
    
    def _format_funding(self, amount_billions: float) -> str:
        """Format funding amount for display"""
        if amount_billions >= 1:
            return f"${amount_billions:.1f}B"
        else:
            return f"${amount_billions * 1000:.0f}M"
