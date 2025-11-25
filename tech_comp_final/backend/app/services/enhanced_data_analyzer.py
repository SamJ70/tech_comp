from typing import Dict, List
import re
from collections import Counter
from datetime import datetime
import json

class EnhancedDataAnalyzer:
    def __init__(self):
        self.current_year = datetime.now().year
    
    def analyze_and_compare(
        self, 
        country1: str, 
        country2: str, 
        domain: str,
        country1_data: Dict,
        country2_data: Dict,
        detail_level: str = "standard"
    ) -> Dict:
        """Enhanced analysis with AI insights"""
        
        # Analyze each country
        analysis1 = self._deep_analyze(country1, domain, country1_data)
        analysis2 = self._deep_analyze(country2, domain, country2_data)
        
        # Generate comparisons
        comparison = self._compare_countries(country1, country2, analysis1, analysis2)
        
        # Generate insights
        insights = self._generate_insights(country1, country2, analysis1, analysis2)
        
        # Overall conclusion
        conclusion = self._generate_conclusion(country1, country2, domain, analysis1, analysis2, comparison)
        
        # Prepare charts data
        charts_data = self._prepare_charts_data(country1, country2, analysis1, analysis2)
        
        return {
            "summary": {
                country1: analysis1["summary"],
                country2: analysis2["summary"]
            },
            "concrete_metrics": {
                country1: analysis1["metrics"],
                country2: analysis2["metrics"]
            },
            "comparison": comparison,
            "overall_analysis": conclusion,
            "key_findings": insights,
            "charts_data": charts_data,
            "data_quality": self._assess_quality(country1_data, country2_data)
        }
    
    def _deep_analyze(self, country: str, domain: str, data: Dict) -> Dict:
        """Deep analysis of country data"""
        combined_text = " ".join(data.get("raw_text", []))
        
        # Extract metrics
        metrics = {
            "funding": self._extract_funding(combined_text),
            "companies": self._extract_companies(combined_text),
            "research": self._extract_research(combined_text),
            "patents": self._extract_patents(combined_text),
            "recent_developments": self._extract_developments(combined_text, country)
        }
        
        # Generate summary
        summary = self._generate_summary(country, domain, metrics)
        
        return {
            "metrics": metrics,
            "summary": summary,
            "score": self._calculate_score(metrics)
        }
    
    def _extract_funding(self, text: str) -> List[str]:
        """Extract funding information"""
        funding_pattern = r'\$\s*(\d+(?:\.\d+)?)\s*(billion|million|trillion)'
        matches = re.findall(funding_pattern, text, re.IGNORECASE)
        
        funding_list = []
        for amount, unit in matches:
            funding_list.append(f"${amount}{unit[0].upper()}")
        
        return sorted(set(funding_list), reverse=True)[:5]
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract company names"""
        # Major tech companies
        major_companies = [
            "Google", "Microsoft", "Amazon", "Apple", "Meta",
            "IBM", "Intel", "NVIDIA", "Tesla", "OpenAI"
        ]
        
        found_companies = []
        for company in major_companies:
            if company.lower() in text.lower():
                found_companies.append(company)
        
        return found_companies[:10]
    
    def _extract_research(self, text: str) -> Dict:
        """Extract research metrics"""
        research_pattern = r'(\d{1,3}(?:,\d{3})*)\s*(?:research\s+)?papers?'
        matches = re.findall(research_pattern, text, re.IGNORECASE)
        
        return {
            "papers": matches[:3] if matches else [],
            "universities": self._extract_universities(text)
        }
    
    def _extract_patents(self, text: str) -> List[str]:
        """Extract patent information"""
        patent_pattern = r'(\d{1,3}(?:,\d{3})*)\s*patents?'
        matches = re.findall(patent_pattern, text, re.IGNORECASE)
        return matches[:5]
    
    def _extract_universities(self, text: str) -> List[str]:
        """Extract university names"""
        uni_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:University|Institute))'
        matches = re.findall(uni_pattern, text)
        return list(set(matches))[:5]
    
    def _extract_developments(self, text: str, country: str) -> List[Dict]:
        """Extract recent developments"""
        developments = []
        sentences = re.split(r'[.!?]+', text)
        
        action_keywords = ["launched", "announced", "developed", "released", "invested"]
        
        for sentence in sentences[:100]:
            if any(kw in sentence.lower() for kw in action_keywords):
                year_match = re.search(r'\b(202[0-5])\b', sentence)
                if year_match and country.lower() in sentence.lower():
                    developments.append({
                        "year": int(year_match.group(1)),
                        "description": sentence.strip()[:200]
                    })
        
        return sorted(developments, key=lambda x: x["year"], reverse=True)[:5]
    
    def _generate_summary(self, country: str, domain: str, metrics: Dict) -> str:
        """Generate country summary"""
        parts = [f"{country}'s {domain} sector"]
        
        if metrics["funding"]:
            parts.append(f"has attracted funding of {', '.join(metrics['funding'][:2])}")
        
        if metrics["companies"]:
            parts.append(f"with major players including {', '.join(metrics['companies'][:3])}")
        
        if metrics["recent_developments"]:
            latest = metrics["recent_developments"][0]
            parts.append(f"Recent activity includes: {latest['description'][:100]}...")
        
        return ". ".join(parts) + "."
    
    def _calculate_score(self, metrics: Dict) -> float:
        """Calculate overall score"""
        score = 0.0
        
        # Funding score
        score += len(metrics["funding"]) * 10
        
        # Companies score
        score += len(metrics["companies"]) * 5
        
        # Research score
        score += len(metrics["research"]["papers"]) * 3
        
        # Recent activity score
        score += len(metrics["recent_developments"]) * 8
        
        return min(score, 100)
    
    def _compare_countries(self, country1: str, country2: str, analysis1: Dict, analysis2: Dict) -> Dict:
        """Generate detailed comparisons"""
        return {
            "funding": f"{country1}: {len(analysis1['metrics']['funding'])} funding events vs {country2}: {len(analysis2['metrics']['funding'])} events",
            "ecosystem": f"{country1} has {len(analysis1['metrics']['companies'])} major companies vs {country2} with {len(analysis2['metrics']['companies'])}",
            "innovation": f"Recent developments: {country1} ({len(analysis1['metrics']['recent_developments'])}) vs {country2} ({len(analysis2['metrics']['recent_developments'])})",
            "overall_score": f"{country1}: {analysis1['score']:.1f}/100 vs {country2}: {analysis2['score']:.1f}/100"
        }
    
    def _generate_insights(self, country1: str, country2: str, analysis1: Dict, analysis2: Dict) -> List[str]:
        """Generate key insights"""
        insights = []
        
        score_diff = abs(analysis1["score"] - analysis2["score"])
        if score_diff > 20:
            leader = country1 if analysis1["score"] > analysis2["score"] else country2
            insights.append(f"{leader} shows significantly stronger ecosystem metrics")
        
        if len(analysis1["metrics"]["funding"]) > len(analysis2["metrics"]["funding"]) * 1.5:
            insights.append(f"{country1} has attracted notably more documented funding")
        elif len(analysis2["metrics"]["funding"]) > len(analysis1["metrics"]["funding"]) * 1.5:
            insights.append(f"{country2} has attracted notably more documented funding")
        
        return insights
    
    def _generate_conclusion(self, country1: str, country2: str, domain: str, 
                           analysis1: Dict, analysis2: Dict, comparison: Dict) -> str:
        """Generate overall conclusion"""
        score1 = analysis1["score"]
        score2 = analysis2["score"]
        
        if abs(score1 - score2) < 15:
            conclusion = f"Both {country1} and {country2} demonstrate competitive capabilities in {domain}. "
            conclusion += f"The analysis reveals similar strength levels with {country1} scoring {score1:.1f}/100 and {country2} scoring {score2:.1f}/100. "
            conclusion += "Each country has distinct advantages in different areas."
        else:
            leader = country1 if score1 > score2 else country2
            follower = country2 if score1 > score2 else country1
            leader_score = max(score1, score2)
            follower_score = min(score1, score2)
            
            conclusion = f"{leader} demonstrates stronger documented performance in {domain}, scoring {leader_score:.1f}/100 compared to {follower}'s {follower_score:.1f}/100. "
            conclusion += f"Key advantages include higher funding levels, more major companies, and greater recent activity. "
            conclusion += f"However, {follower} continues to develop its ecosystem with notable initiatives."
        
        conclusion += f"\n\n**Important Note**: This analysis is based on publicly available Wikipedia data and represents documented information rather than comprehensive capability assessment."
        
        return conclusion
    
    def _prepare_charts_data(self, country1: str, country2: str, analysis1: Dict, analysis2: Dict) -> Dict:
        """Prepare data for frontend charts"""
        return {
            "scores": {
                "labels": [country1, country2],
                "values": [analysis1["score"], analysis2["score"]]
            },
            "metrics": {
                "labels": ["Funding", "Companies", "Research", "Recent Activity"],
                "country1": [
                    len(analysis1["metrics"]["funding"]),
                    len(analysis1["metrics"]["companies"]),
                    len(analysis1["metrics"]["research"]["papers"]),
                    len(analysis1["metrics"]["recent_developments"])
                ],
                "country2": [
                    len(analysis2["metrics"]["funding"]),
                    len(analysis2["metrics"]["companies"]),
                    len(analysis2["metrics"]["research"]["papers"]),
                    len(analysis2["metrics"]["recent_developments"])
                ]
            }
        }
    
    def _assess_quality(self, data1: Dict, data2: Dict) -> Dict:
        """Assess data quality"""
        warnings = []
        
        text1_len = sum(len(t) for t in data1.get("raw_text", []))
        text2_len = sum(len(t) for t in data2.get("raw_text", []))
        
        if text1_len < 5000:
            warnings.append("Limited data available for first country")
        if text2_len < 5000:
            warnings.append("Limited data available for second country")
        
        if max(text1_len, text2_len) / max(min(text1_len, text2_len), 1) > 2:
            warnings.append("Significant data imbalance between countries")
        
        confidence = "high" if not warnings else "medium" if len(warnings) <= 2 else "low"
        
        return {
            "confidence": confidence,
            "warnings": warnings,
            "sources": {
                "country1": len(data1.get("raw_text", [])),
                "country2": len(data2.get("raw_text", []))
            }
        }