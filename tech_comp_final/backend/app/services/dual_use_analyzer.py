# backend/app/services/dual_use_analyzer.py
from typing import Dict, List, Tuple
import re
from datetime import datetime

class DualUseAnalyzer:
    """Analyzes technology for dual-use (civilian/military) applications"""
    
    def __init__(self):
        # Wassenaar Arrangement Categories (simplified version)
        self.wassenaar_categories = {
            "AI_ML": {
                "keywords": ["artificial intelligence", "machine learning", "neural network", "deep learning"],
                "military_indicators": ["autonomous weapons", "target recognition", "military ai", "defense ai"],
                "safe_limit": "civilian research only",
                "category": "Category 4 - Computers"
            },
            "QUANTUM": {
                "keywords": ["quantum computing", "quantum cryptography", "quantum communication"],
                "military_indicators": ["quantum encryption", "military quantum", "secure communications"],
                "safe_limit": "research and civilian communications",
                "category": "Category 5 Part 2 - Information Security"
            },
            "ROBOTICS": {
                "keywords": ["robotics", "autonomous systems", "drones", "uav"],
                "military_indicators": ["military drone", "combat robot", "autonomous weapon", "lethal autonomous"],
                "safe_limit": "industrial and civilian use only",
                "category": "Category 2 - Materials Processing"
            },
            "CYBER": {
                "keywords": ["cybersecurity", "intrusion software", "network surveillance"],
                "military_indicators": ["cyber warfare", "offensive cyber", "cyber weapon"],
                "safe_limit": "defensive cybersecurity only",
                "category": "Category 5 Part 2 - Information Security"
            },
            "BIOTECH": {
                "keywords": ["biotechnology", "genetic engineering", "crispr", "gene editing"],
                "military_indicators": ["biological weapon", "bioweapon", "military biological"],
                "safe_limit": "medical and agricultural research only",
                "category": "Category 1 - Materials, Chemicals, Microorganisms & Toxins"
            },
            "SPACE": {
                "keywords": ["satellite", "space technology", "rocket", "launch vehicle"],
                "military_indicators": ["military satellite", "spy satellite", "reconnaissance satellite", "anti-satellite"],
                "safe_limit": "civilian space exploration and communications",
                "category": "Category 9 - Aerospace and Propulsion"
            },
            "TELECOM": {
                "keywords": ["5g", "telecommunications", "network infrastructure"],
                "military_indicators": ["military communications", "secure military network"],
                "safe_limit": "civilian communications infrastructure",
                "category": "Category 5 Part 1 - Telecommunications"
            },
            "ENERGY": {
                "keywords": ["nuclear energy", "fusion", "advanced reactors"],
                "military_indicators": ["nuclear weapon", "weapons-grade", "enrichment"],
                "safe_limit": "civilian power generation only",
                "category": "Category 0 - Nuclear Materials"
            }
        }
        
        # Risk levels
        self.risk_levels = {
            "LOW": "Within safe limits - primarily civilian applications",
            "MODERATE": "Some dual-use concerns - requires monitoring",
            "HIGH": "Significant military applications detected",
            "CRITICAL": "Potential weapons development or prohibited activities"
        }
    
    def analyze_dual_use(self, country: str, domain: str, data: Dict, time_range: int = None) -> Dict:
        """
        Analyze technology for dual-use applications
        
        Args:
            country: Country name
            domain: Technology domain
            data: Fetched data with text content
            time_range: Optional year range to filter (e.g., 5 for last 5 years)
        
        Returns:
            Analysis results with risk assessment
        """
        combined_text = " ".join(data.get("raw_text", [])).lower()
        current_year = datetime.now().year
        
        # Filter by time range if specified
        if time_range:
            filtered_text = self._filter_by_time_range(combined_text, current_year - time_range, current_year)
        else:
            filtered_text = combined_text
        
        # Identify relevant Wassenaar category
        category_match = self._identify_wassenaar_category(domain)
        
        if not category_match:
            return {
                "risk_level": "LOW",
                "wassenaar_category": "Not classified",
                "compliance_status": "N/A",
                "findings": ["Domain not in dual-use categories"],
                "military_indicators": [],
                "civilian_indicators": [],
                "recommendations": ["Continue monitoring general technology development"]
            }
        
        # Analyze content
        military_indicators = self._find_military_indicators(filtered_text, category_match)
        civilian_indicators = self._find_civilian_indicators(filtered_text, category_match)
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(military_indicators, civilian_indicators)
        
        # Generate compliance assessment
        compliance = self._assess_compliance(risk_level, category_match)
        
        # Extract specific developments
        developments = self._extract_developments(filtered_text, country, time_range)
        
        return {
            "risk_level": risk_level,
            "risk_description": self.risk_levels[risk_level],
            "wassenaar_category": category_match["category"],
            "safe_limit": category_match["safe_limit"],
            "compliance_status": compliance["status"],
            "compliance_notes": compliance["notes"],
            "military_indicators": military_indicators,
            "civilian_indicators": civilian_indicators,
            "developments": developments,
            "recommendations": self._generate_recommendations(risk_level, military_indicators),
            "monitoring_required": risk_level in ["MODERATE", "HIGH", "CRITICAL"]
        }
    
    def _identify_wassenaar_category(self, domain: str) -> Dict:
        """Match domain to Wassenaar category"""
        domain_lower = domain.lower()
        
        for category, info in self.wassenaar_categories.items():
            if any(keyword in domain_lower for keyword in info["keywords"]):
                return info
        
        return None
    
    def _find_military_indicators(self, text: str, category: Dict) -> List[Dict]:
        """Find military application indicators"""
        indicators = []
        
        for indicator in category["military_indicators"]:
            if indicator in text:
                # Find context
                pattern = rf'.{{0,100}}{re.escape(indicator)}.{{0,100}}'
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches[:3]:  # Limit to 3 examples
                    indicators.append({
                        "indicator": indicator,
                        "context": match.strip(),
                        "severity": "HIGH" if any(word in indicator for word in ["weapon", "combat", "warfare"]) else "MODERATE"
                    })
        
        return indicators
    
    def _find_civilian_indicators(self, text: str, category: Dict) -> List[str]:
        """Find civilian application indicators"""
        civilian_keywords = [
            "research", "university", "academic", "medical", "healthcare",
            "commercial", "consumer", "industrial", "civilian", "peaceful",
            "education", "scientific", "innovation", "startup", "business"
        ]
        
        indicators = []
        for keyword in civilian_keywords:
            if keyword in text:
                indicators.append(keyword)
        
        return list(set(indicators))[:10]
    
    def _calculate_risk_level(self, military_indicators: List, civilian_indicators: List) -> str:
        """Calculate overall risk level"""
        mil_count = len(military_indicators)
        civ_count = len(civilian_indicators)
        
        # Check for high-severity military indicators
        high_severity = sum(1 for ind in military_indicators if ind.get("severity") == "HIGH")
        
        if high_severity >= 2:
            return "CRITICAL"
        elif mil_count >= 5 or (mil_count >= 3 and civ_count < 3):
            return "HIGH"
        elif mil_count >= 2 or (mil_count >= 1 and civ_count < 5):
            return "MODERATE"
        else:
            return "LOW"
    
    def _assess_compliance(self, risk_level: str, category: Dict) -> Dict:
        """Assess compliance with safe limits"""
        if risk_level == "LOW":
            return {
                "status": "COMPLIANT",
                "notes": f"Development appears within safe limits: {category['safe_limit']}"
            }
        elif risk_level == "MODERATE":
            return {
                "status": "MONITORING_REQUIRED",
                "notes": "Some dual-use concerns detected. Continued monitoring recommended."
            }
        elif risk_level == "HIGH":
            return {
                "status": "NON_COMPLIANT",
                "notes": "Significant military applications detected. May exceed safe civilian use limits."
            }
        else:  # CRITICAL
            return {
                "status": "CRITICAL_VIOLATION",
                "notes": "Potential weapons development or prohibited activities detected. Immediate review required."
            }
    
    def _extract_developments(self, text: str, country: str, time_range: int) -> List[Dict]:
        """Extract specific technology developments"""
        developments = []
        
        # Find sentences with years
        year_pattern = r'\b(20\d{2})\b'
        sentences = re.split(r'[.!?]+', text)
        
        current_year = datetime.now().year
        min_year = current_year - time_range if time_range else 2015
        
        for sentence in sentences:
            years = re.findall(year_pattern, sentence)
            for year_str in years:
                year = int(year_str)
                if min_year <= year <= current_year:
                    if country.lower() in sentence.lower() and len(sentence) > 50:
                        developments.append({
                            "year": year,
                            "description": sentence.strip()[:300],
                            "relevance": "high" if any(word in sentence.lower() for word in ["launched", "developed", "announced"]) else "medium"
                        })
        
        # Sort by year descending
        developments.sort(key=lambda x: x["year"], reverse=True)
        return developments[:15]
    
    def _generate_recommendations(self, risk_level: str, military_indicators: List) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if risk_level == "CRITICAL":
            recommendations.extend([
                "Immediate investigation required into potential weapons development",
                "Review international export control compliance",
                "Engage with relevant authorities for verification"
            ])
        elif risk_level == "HIGH":
            recommendations.extend([
                "Enhanced monitoring of military applications",
                "Verify end-use of exported technologies",
                "Regular compliance audits recommended"
            ])
        elif risk_level == "MODERATE":
            recommendations.extend([
                "Continue routine monitoring",
                "Track developments in military applications",
                "Maintain awareness of dual-use concerns"
            ])
        else:
            recommendations.append("Standard monitoring procedures sufficient")
        
        if military_indicators:
            recommendations.append(f"Investigate {len(military_indicators)} military application indicators")
        
        return recommendations
    
    def _filter_by_time_range(self, text: str, start_year: int, end_year: int) -> str:
        """Filter text to only include content from specified year range"""
        sentences = re.split(r'[.!?]+', text)
        filtered = []
        
        for sentence in sentences:
            years = re.findall(r'\b(20\d{2})\b', sentence)
            if any(start_year <= int(year) <= end_year for year in years):
                filtered.append(sentence)
        
        return ". ".join(filtered)