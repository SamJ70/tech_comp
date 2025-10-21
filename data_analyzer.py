from typing import Dict, List
import re
from collections import Counter
from datetime import datetime

class ImprovedDataAnalyzer:
    def __init__(self):
        self.current_year = datetime.now().year
    
    def analyze_and_compare(
        self, 
        country1: str, 
        country2: str, 
        domain: str,
        country1_data: Dict,
        country2_data: Dict
    ) -> Dict:
        """Perform evidence-based analysis and comparison"""
        
        # Analyze each country
        analysis1 = self._analyze_country_data(country1, domain, country1_data)
        analysis2 = self._analyze_country_data(country2, domain, country2_data)
        
        # Generate comparison
        comparison = self._generate_evidence_based_comparison(
            country1, country2, domain, analysis1, analysis2
        )
        
        # Overall conclusion
        overall = self._generate_balanced_conclusion(
            country1, country2, domain, analysis1, analysis2, comparison
        )
        
        # Validate and add quality metrics
        result = {
            "summary": {
                country1: analysis1["summary"],
                country2: analysis2["summary"]
            },
            "concrete_metrics": {
                country1: analysis1["concrete_metrics"],
                country2: analysis2["concrete_metrics"]
            },
            "comparison": comparison,
            "overall_analysis": overall,
            "resources": {
                country1: analysis1["key_entities"],
                country2: analysis2["key_entities"]
            },
            "news": analysis1["highlights"] + analysis2["highlights"]
        }
        
        # Add data quality assessment
        result = self._add_quality_assessment(result, country1_data, country2_data)
        
        return result
    
    def _analyze_country_data(self, country: str, domain: str, data: Dict) -> Dict:
        """Extract concrete, verifiable metrics"""
        combined_text = " ".join(data.get("raw_text", []))
        text_length = len(combined_text)
        
        # Extract concrete metrics
        concrete_metrics = self._extract_concrete_metrics(combined_text, domain)
        
        # Extract companies and valuations
        companies = self._extract_companies_with_context(combined_text, domain)
        
        # Extract recent developments with dates
        recent_dev = self._extract_dated_developments(combined_text, domain, country)
        
        # Generate evidence-based summary
        summary = self._generate_evidence_summary(
            country, domain, concrete_metrics, companies, recent_dev
        )
        
        # Extract key entities
        entities = self._extract_key_entities(combined_text, country)
        
        # Extract highlights
        highlights = self._extract_highlights(combined_text, domain, country)
        
        return {
            "summary": summary,
            "concrete_metrics": concrete_metrics,
            "companies": companies[:15],
            "recent_developments": recent_dev[:8],
            "key_entities": entities,
            "highlights": highlights,
            "text_length": text_length,
            "source_count": len(data.get("raw_text", [])),
            "avg_relevance": sum(data.get("relevance_scores", [0])) / max(len(data.get("relevance_scores", [0])), 1)
        }
    
    def _extract_concrete_metrics(self, text: str, domain: str) -> Dict:
        """Extract specific, verifiable numbers"""
        metrics = {
            "funding_amounts": [],
            "company_valuations": [],
            "patent_counts": [],
            "research_output": [],
            "market_size": [],
            "growth_rates": [],
            "investment_deals": []
        }
        
        # Funding: "$5 billion funding" or "received $2.3 million"
        funding_pattern = r'(?:received|raised|secured|invested|funding of|investment of)?\s*\$?(\d+(?:\.\d+)?)\s*(billion|million|trillion)\s*(?:in funding|investment|capital)?'
        for match in re.finditer(funding_pattern, text, re.IGNORECASE):
            amount = float(match.group(1))
            unit = match.group(2).lower()
            
            if unit == "billion":
                amount_display = f"${amount}B"
            elif unit == "million":
                amount_display = f"${amount}M"
            else:
                amount_display = f"${amount}T"
            
            metrics["funding_amounts"].append(amount_display)
        
        # Patents: "filed 10,000 patents" or "12,345 AI patents"
        patent_pattern = r'(\d{1,3}(?:,\d{3})*|\d+)\s+(?:AI|technology|tech|robotics|software)?\s*patents?'
        matches = re.findall(patent_pattern, text, re.IGNORECASE)
        metrics["patent_counts"] = [m.replace(',', '') for m in matches[:5]]
        
        # Market size: "market worth $50 billion"
        market_pattern = r'market\s+(?:worth|size|valued at)\s+\$?(\d+(?:\.\d+)?)\s*(billion|million|trillion)'
        for match in re.finditer(market_pattern, text, re.IGNORECASE):
            amount = float(match.group(1))
            unit = match.group(2).lower()
            metrics["market_size"].append(f"${amount}{unit[0].upper()}")
        
        # Growth rates: "30% growth" or "grew by 45 percent"
        growth_pattern = r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:growth|increase|rise)'
        matches = re.findall(growth_pattern, text, re.IGNORECASE)
        metrics["growth_rates"] = [f"{m}%" for m in matches[:5]]
        
        # Research output: "published 5,000 papers"
        research_pattern = r'(?:published|produced)\s+(\d{1,3}(?:,\d{3})*)\s+(?:research\s+)?papers?'
        matches = re.findall(research_pattern, text, re.IGNORECASE)
        metrics["research_output"] = [m for m in matches[:5]]
        
        # Count investment deals
        deal_keywords = ["acquired", "acquisition", "invested in", "partnership with", "joint venture"]
        metrics["investment_deals"] = [kw for kw in deal_keywords if kw in text.lower()]
        
        return metrics
    
    def _extract_companies_with_context(self, text: str, domain: str) -> List[Dict]:
        """Extract companies with surrounding context"""
        companies = []
        
        # Major tech companies
        major_companies = [
            "Google", "Microsoft", "Amazon", "Apple", "Meta", "Facebook",
            "IBM", "Intel", "NVIDIA", "OpenAI", "DeepMind", "Tesla",
            "Anthropic", "Baidu", "Alibaba", "Tencent", "Samsung"
        ]
        
        # Find major companies with context
        for company in major_companies:
            pattern = rf'({company})(?:\s+\w+){{0,10}}(?:developed|launched|announced|invested|acquired|released|pioneered)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].strip()
                
                companies.append({
                    "name": company,
                    "context": context,
                    "is_major": True
                })
        
        # Find other companies
        company_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Technologies|Labs|Systems|Solutions|AI)))\b'
        other_companies = re.findall(company_pattern, text)
        
        company_counts = Counter(other_companies)
        for comp, count in company_counts.most_common(20):
            if comp not in [c["name"] for c in companies]:
                companies.append({
                    "name": comp,
                    "mentions": count,
                    "is_major": False
                })
        
        return companies
    
    def _extract_dated_developments(self, text: str, domain: str, country: str) -> List[Dict]:
        """Extract developments with specific dates"""
        developments = []
        sentences = re.split(r'[.!?]+', text)
        
        # Recent years
        recent_years = list(range(2020, self.current_year + 2))
        
        # Action keywords
        action_keywords = [
            "launched", "announced", "developed", "released", "introduced",
            "unveiled", "established", "created", "invested", "acquired",
            "signed", "approved", "implemented", "initiated"
        ]
        
        for sentence in sentences:
            # Must have year
            year_match = re.search(r'\b(20\d{2})\b', sentence)
            if not year_match:
                continue
            
            year = int(year_match.group(1))
            if year not in recent_years:
                continue
            
            # Must have action
            if not any(kw in sentence.lower() for kw in action_keywords):
                continue
            
            # Should be relevant
            is_relevant = (
                domain.lower() in sentence.lower() or
                country.lower() in sentence.lower() or
                any(tech in sentence.lower() for tech in ["technology", "ai", "innovation", "research"])
            )
            
            if is_relevant and len(sentence.strip()) > 50:
                # Extract funding if present
                funding_match = re.search(r'\$(\d+(?:\.\d+)?)\s*(billion|million)', sentence)
                funding = f"${funding_match.group(1)}{funding_match.group(2)[0].upper()}" if funding_match else None
                
                developments.append({
                    "year": year,
                    "description": sentence.strip()[:250],
                    "funding": funding
                })
        
        # Sort by year (newest first)
        developments.sort(key=lambda x: x["year"], reverse=True)
        return developments
    
    def _generate_evidence_summary(
        self, 
        country: str, 
        domain: str, 
        metrics: Dict,
        companies: List[Dict],
        developments: List[Dict]
    ) -> str:
        """Generate summary based on concrete evidence"""
        summary_parts = []
        
        # Start with country and domain
        summary_parts.append(f"{country} in {domain}:")
        
        # Add funding info
        if metrics["funding_amounts"]:
            top_funding = sorted(metrics["funding_amounts"], 
                               key=lambda x: float(x.replace('$','').replace('B','').replace('M','').replace('T','')),
                               reverse=True)[:3]
            summary_parts.append(f"Notable funding includes {', '.join(top_funding)}.")
        
        # Add major companies
        major_companies = [c["name"] for c in companies if c.get("is_major", False)]
        if major_companies:
            summary_parts.append(f"Major players include {', '.join(major_companies[:5])}.")
        
        # Add recent development
        if developments:
            latest = developments[0]
            summary_parts.append(f"Recent: {latest['description'][:200]}")
        
        # Add market metrics
        if metrics["market_size"]:
            summary_parts.append(f"Market size: {metrics['market_size'][0]}.")
        
        if metrics["growth_rates"]:
            summary_parts.append(f"Growth rate: {metrics['growth_rates'][0]}.")
        
        return " ".join(summary_parts)[:600]
    
    def _extract_key_entities(self, text: str, country: str) -> List[str]:
        """Extract organizations and institutions"""
        entities = []
        
        # Universities and research institutes
        edu_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:University|Institute|College|Laboratory|Lab|Research Center))\b'
        edu_matches = re.findall(edu_pattern, text)
        entities.extend(list(set(edu_matches))[:5])
        
        # Government bodies
        gov_pattern = r'\b((?:Ministry|Department|Agency|Commission|Bureau)\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        gov_matches = re.findall(gov_pattern, text)
        entities.extend(list(set(gov_matches))[:3])
        
        return entities[:8]
    
    def _extract_highlights(self, text: str, domain: str, country: str) -> List[Dict]:
        """Extract newsworthy highlights"""
        sentences = re.split(r'[.!?]+', text)
        highlights = []
        
        news_keywords = [
            "announced", "launched", "breakthrough", "first", "largest",
            "leading", "pioneering", "revolutionary", "milestone"
        ]
        
        for sentence in sentences[:200]:
            if any(kw in sentence.lower() for kw in news_keywords):
                has_year = bool(re.search(r'20\d{2}', sentence))
                is_relevant = (domain.lower() in sentence.lower() or 
                             country.lower() in sentence.lower())
                
                if is_relevant and len(sentence.strip()) > 60:
                    highlights.append({
                        "source": "Analysis",
                        "headline": sentence.strip()[:200],
                        "recent": has_year
                    })
                    
                    if len(highlights) >= 8:
                        break
        
        return sorted(highlights, key=lambda x: x["recent"], reverse=True)
    
    def _generate_evidence_based_comparison(
        self,
        country1: str,
        country2: str,
        domain: str,
        analysis1: Dict,
        analysis2: Dict
    ) -> Dict:
        """Compare based on concrete evidence"""
        comparison = {}
        
        metrics1 = analysis1["concrete_metrics"]
        metrics2 = analysis2["concrete_metrics"]
        
        # Compare funding
        funding1 = self._get_max_funding(metrics1["funding_amounts"])
        funding2 = self._get_max_funding(metrics2["funding_amounts"])
        
        if funding1 > 0 or funding2 > 0:
            if funding1 > funding2 * 1.5:
                comparison["funding"] = f"{country1} shows significantly higher funding ({self._format_amount(funding1)} vs {self._format_amount(funding2)})"
            elif funding2 > funding1 * 1.5:
                comparison["funding"] = f"{country2} shows significantly higher funding ({self._format_amount(funding2)} vs {self._format_amount(funding1)})"
            else:
                comparison["funding"] = f"Comparable funding levels ({self._format_amount(funding1)} vs {self._format_amount(funding2)})"
        
        # Compare companies
        major1 = len([c for c in analysis1["companies"] if c.get("is_major", False)])
        major2 = len([c for c in analysis2["companies"] if c.get("is_major", False)])
        
        if major1 > 0 or major2 > 0:
            comparison["major_companies"] = f"{country1}: {major1} major tech companies | {country2}: {major2} major tech companies"
        
        # Compare patents
        if metrics1["patent_counts"] or metrics2["patent_counts"]:
            patents1 = max([int(p.replace(',','')) for p in metrics1["patent_counts"]], default=0)
            patents2 = max([int(p.replace(',','')) for p in metrics2["patent_counts"]], default=0)
            
            if patents1 > 0 or patents2 > 0:
                comparison["patents"] = f"Patent activity: {country1} ({patents1:,}) vs {country2} ({patents2:,})"
        
        # Compare recent activity
        dev1 = len(analysis1["recent_developments"])
        dev2 = len(analysis2["recent_developments"])
        comparison["recent_activity"] = f"Recent developments: {country1} ({dev1}) vs {country2} ({dev2})"
        
        # Compare market size
        market1 = self._get_max_market(metrics1["market_size"])
        market2 = self._get_max_market(metrics2["market_size"])
        
        if market1 > 0 or market2 > 0:
            comparison["market_size"] = f"Market size: {country1} ({self._format_amount(market1)}) vs {country2} ({self._format_amount(market2)})"
        
        # Compare growth
        if metrics1["growth_rates"] or metrics2["growth_rates"]:
            growth1 = max([float(g.replace('%','')) for g in metrics1["growth_rates"]], default=0)
            growth2 = max([float(g.replace('%','')) for g in metrics2["growth_rates"]], default=0)
            
            if growth1 > 0 or growth2 > 0:
                comparison["growth"] = f"Growth rates: {country1} ({growth1}%) vs {country2} ({growth2}%)"
        
        return comparison
    
    def _generate_balanced_conclusion(
        self,
        country1: str,
        country2: str,
        domain: str,
        analysis1: Dict,
        analysis2: Dict,
        comparison: Dict
    ) -> str:
        """Generate evidence-based conclusion"""
        
        # Score countries based on concrete evidence
        score1 = 0
        score2 = 0
        evidence = []
        
        metrics1 = analysis1["concrete_metrics"]
        metrics2 = analysis2["concrete_metrics"]
        
        # Funding comparison
        funding1 = self._get_max_funding(metrics1["funding_amounts"])
        funding2 = self._get_max_funding(metrics2["funding_amounts"])
        
        if funding1 > funding2 * 1.5:
            score1 += 2
            evidence.append(f"{country1} has higher documented funding levels")
        elif funding2 > funding1 * 1.5:
            score2 += 2
            evidence.append(f"{country2} has higher documented funding levels")
        
        # Major companies
        major1 = len([c for c in analysis1["companies"] if c.get("is_major", False)])
        major2 = len([c for c in analysis2["companies"] if c.get("is_major", False)])
        
        if major1 > major2 * 1.3:
            score1 += 2
            evidence.append(f"{country1} has more global tech leaders ({major1} vs {major2})")
        elif major2 > major1 * 1.3:
            score2 += 2
            evidence.append(f"{country2} has more global tech leaders ({major2} vs {major1})")
        
        # Recent developments
        dev1 = len(analysis1["recent_developments"])
        dev2 = len(analysis2["recent_developments"])
        
        if dev1 > dev2 * 1.3:
            score1 += 1
            evidence.append(f"{country1} shows more recent activity ({dev1} vs {dev2} developments)")
        elif dev2 > dev1 * 1.3:
            score2 += 1
            evidence.append(f"{country2} shows more recent activity ({dev2} vs {dev1} developments)")
        
        # Patents
        patents1 = max([int(p.replace(',','')) for p in metrics1["patent_counts"]], default=0)
        patents2 = max([int(p.replace(',','')) for p in metrics2["patent_counts"]], default=0)
        
        if patents1 > patents2 * 1.5:
            score1 += 1
            evidence.append(f"{country1} has higher patent activity")
        elif patents2 > patents1 * 1.5:
            score2 += 1
            evidence.append(f"{country2} has higher patent activity")
        
        # Generate conclusion
        if score1 > score2 + 1:
            leader = country1
            follower = country2
        elif score2 > score1 + 1:
            leader = country2
            follower = country1
        else:
            # Balanced
            return (
                f"Both {country1} and {country2} demonstrate strong capabilities in {domain}. "
                f"The analysis shows competitive positioning across multiple dimensions:\n\n"
                f"• {country1}: {major1} major tech companies, {dev1} recent developments\n"
                f"• {country2}: {major2} major tech companies, {dev2} recent developments\n\n"
                f"Each country has distinct strengths, and the comparison depends on specific metrics prioritized. "
                f"Note: Analysis based on publicly available Wikipedia data as of {datetime.now().strftime('%B %Y')}."
            )
        
        # Leader conclusion
        conclusion = (
            f"Based on documented evidence, {leader} demonstrates stronger indicators in {domain}:\n\n"
        )
        
        for ev in evidence:
            if leader in ev:
                conclusion += f"• {ev}\n"
        
        conclusion += (
            f"\n{follower} continues to develop its {domain} capabilities with "
            f"{dev2 if leader == country1 else dev1} recent initiatives documented. "
            f"\n\n**Important Context:**\n"
            f"• This analysis is based on publicly available Wikipedia data\n"
            f"• Data completeness varies by country (source relevance: {analysis1['avg_relevance']:.1f}/10 vs {analysis2['avg_relevance']:.1f}/10)\n"
            f"• Results represent documented information, not comprehensive capability assessment\n"
            f"• Some countries may have less comprehensive English-language documentation"
        )
        
        return conclusion
    
    def _add_quality_assessment(self, result: Dict, data1: Dict, data2: Dict) -> Dict:
        """Add data quality warnings and confidence scores"""
        warnings = []
        
        # Check data volumes
        text1 = sum(len(t) for t in data1.get("raw_text", []))
        text2 = sum(len(t) for t in data2.get("raw_text", []))
        
        if text1 < 3000:
            warnings.append(f"Limited data for {list(result['summary'].keys())[0]} - comparison may be incomplete")
        if text2 < 3000:
            warnings.append(f"Limited data for {list(result['summary'].keys())[1]} - comparison may be incomplete")
        
        # Check data balance
        ratio = max(text1, text2) / max(min(text1, text2), 1)
        if ratio > 2.5:
            warnings.append(f"Data imbalance detected ({ratio:.1f}x difference) - may affect comparison fairness")
        
        # Check relevance scores
        relevance1 = sum(data1.get("relevance_scores", [0])) / max(len(data1.get("relevance_scores", [0])), 1)
        relevance2 = sum(data2.get("relevance_scores", [0])) / max(len(data2.get("relevance_scores", [0])), 1)
        
        if relevance1 < 3.0 or relevance2 < 3.0:
            warnings.append("Some sources have low relevance scores - findings may be less specific")
        
        # Check if meaningful differences exist
        metrics1 = result["concrete_metrics"][list(result['summary'].keys())[0]]
        metrics2 = result["concrete_metrics"][list(result['summary'].keys())[1]]
        
        has_concrete = (
            metrics1["funding_amounts"] or metrics2["funding_amounts"] or
            metrics1["patent_counts"] or metrics2["patent_counts"] or
            metrics1["market_size"] or metrics2["market_size"]
        )
        
        if not has_concrete:
            warnings.append("Limited concrete metrics found - analysis relies more on qualitative factors")
        
        # Confidence scoring
        if not warnings:
            confidence = "high"
        elif len(warnings) <= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        result["data_quality"] = {
            "warnings": warnings,
            "confidence": confidence,
            "sources": {
                list(result['summary'].keys())[0]: len(data1.get("raw_text", [])),
                list(result['summary'].keys())[1]: len(data2.get("raw_text", []))
            },
            "relevance_scores": {
                list(result['summary'].keys())[0]: round(relevance1, 2),
                list(result['summary'].keys())[1]: round(relevance2, 2)
            }
        }
        
        return result
    
    def _get_max_funding(self, funding_list: List[str]) -> float:
        """Get maximum funding in billions"""
        max_val = 0.0
        for item in funding_list:
            try:
                val_str = item.replace('$', '').strip()
                if 'B' in val_str:
                    val = float(val_str.replace('B', ''))
                elif 'M' in val_str:
                    val = float(val_str.replace('M', '')) / 1000
                elif 'T' in val_str:
                    val = float(val_str.replace('T', '')) * 1000
                else:
                    continue
                max_val = max(max_val, val)
            except (ValueError, AttributeError):
                continue
        return max_val
    
    def _get_max_market(self, market_list: List[str]) -> float:
        """Get maximum market size in billions"""
        return self._get_max_funding(market_list)
    
    def _format_amount(self, amount: float) -> str:
        """Format monetary amount"""
        if amount == 0:
            return "N/A"
        elif amount >= 1:
            return f"${amount:.1f}B"
        else:
            return f"${amount * 1000:.0f}M"