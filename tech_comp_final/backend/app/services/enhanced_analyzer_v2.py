# backend/app/services/enhanced_analyzer_v2.py
from typing import Dict, List, Optional
import re
from datetime import datetime
import asyncio

class WassenarrClassifier:
    """Classifies technologies against Wassenaar Arrangement categories"""
    
    CATEGORIES = {
        'ML3': {
            'keywords': ['imaging', 'camera', 'sensor', 'optics', 'thermal'],
            'risk_indicators': ['military grade', 'surveillance', 'targeting']
        },
        'ML7': {
            'keywords': ['navigation', 'gps', 'inertial', 'guidance', 'positioning'],
            'risk_indicators': ['missile', 'autonomous', 'drone', 'uav']
        },
        'ML11': {
            'keywords': ['electronics', 'semiconductor', 'microchip', 'processor'],
            'risk_indicators': ['radiation hardened', 'military spec', 'secure']
        },
        'ML21': {
            'keywords': ['software', 'algorithm', 'ai', 'machine learning', 'neural'],
            'risk_indicators': ['autonomous weapons', 'targeting', 'reconnaissance']
        },
        '5A001': {
            'keywords': ['telecommunications', '5g', 'network', 'communication'],
            'risk_indicators': ['encrypted', 'secure', 'military comm']
        },
        '5D001': {
            'keywords': ['cybersecurity', 'encryption', 'intrusion', 'malware'],
            'risk_indicators': ['offensive', 'exploit', 'weapon']
        }
    }
    
    def classify(self, text: str) -> List[Dict]:
        """Classify technology against Wassenaar categories"""
        text_lower = text.lower()
        classifications = []
        
        for category, config in self.CATEGORIES.items():
            keyword_matches = sum(1 for kw in config['keywords'] if kw in text_lower)
            risk_matches = sum(1 for ri in config['risk_indicators'] if ri in text_lower)
            
            if keyword_matches > 0:
                risk_level = self._calculate_risk(keyword_matches, risk_matches)
                classifications.append({
                    'category': category,
                    'confidence': min(keyword_matches / len(config['keywords']), 1.0),
                    'risk_level': risk_level,
                    'risk_score': risk_matches,
                    'military_indicators': risk_matches > 0
                })
        
        return sorted(classifications, key=lambda x: x['confidence'], reverse=True)
    
    def _calculate_risk(self, keyword_score: int, risk_score: int) -> str:
        if risk_score >= 2:
            return 'HIGH'
        elif risk_score == 1 or keyword_score >= 3:
            return 'MEDIUM'
        return 'LOW'


class FactVerifier:
    """GAN-inspired fact verification using cross-source validation"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    async def verify_claim(self, claim: str, sources: List[Dict]) -> Dict:
        """
        Verify a technological claim against multiple sources
        Uses discriminator-like approach to classify as verified/unverified
        """
        # Extract key facts from claim
        facts = self._extract_facts(claim)
        
        # Cross-reference with sources
        verification_scores = []
        for fact in facts:
            score = await self._cross_reference(fact, sources)
            verification_scores.append(score)
        
        avg_confidence = sum(verification_scores) / len(verification_scores) if verification_scores else 0
        
        return {
            'claim': claim,
            'verified': avg_confidence >= self.confidence_threshold,
            'confidence': avg_confidence,
            'source_count': len(sources),
            'corroborating_sources': sum(1 for s in verification_scores if s > 0.5)
        }
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract verifiable facts from text"""
        # Simple fact extraction (can be enhanced with NLP)
        sentences = re.split(r'[.!?]+', text)
        facts = []
        
        fact_indicators = ['developed', 'announced', 'launched', 'achieved', 'demonstrated']
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in fact_indicators):
                facts.append(sentence.strip())
        
        return facts
    
    async def _cross_reference(self, fact: str, sources: List[Dict]) -> float:
        """Cross-reference fact against sources"""
        matches = 0
        fact_lower = fact.lower()
        
        for source in sources:
            source_text = source.get('text', '').lower()
            # Check for semantic similarity (simplified)
            similarity = self._calculate_similarity(fact_lower, source_text)
            if similarity > 0.3:
                matches += 1
        
        return min(matches / max(len(sources), 1), 1.0)
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple similarity calculation (can be enhanced with embeddings)"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0


class TemporalAnalyzer:
    """Analyze technological developments over time"""
    
    def analyze_timeline(self, data: List[Dict], years: int) -> List[Dict]:
        """Generate year-by-year analysis"""
        current_year = datetime.now().year
        timeline = []
        
        for year in range(current_year - years, current_year + 1):
            year_data = [d for d in data if self._extract_year(d) == year]
            
            analysis = {
                'year': year,
                'total_developments': len(year_data),
                'civilian_projects': self._count_civilian(year_data),
                'military_linked': self._count_military(year_data),
                'dual_use': self._count_dual_use(year_data),
                'wassenaar_flags': self._count_wassenaar(year_data),
                'key_developments': self._extract_key_developments(year_data)
            }
            timeline.append(analysis)
        
        return timeline
    
    def _extract_year(self, data: Dict) -> Optional[int]:
        """Extract year from data"""
        text = data.get('text', '')
        years = re.findall(r'\b(20\d{2})\b', text)
        return int(years[0]) if years else None
    
    def _count_civilian(self, data: List[Dict]) -> int:
        """Count civilian-focused projects"""
        civilian_keywords = ['medical', 'healthcare', 'education', 'consumer', 'commercial']
        count = 0
        for item in data:
            text = item.get('text', '').lower()
            if any(kw in text for kw in civilian_keywords):
                count += 1
        return count
    
    def _count_military(self, data: List[Dict]) -> int:
        """Count military-linked projects"""
        military_keywords = ['military', 'defense', 'weapon', 'surveillance', 'tactical']
        count = 0
        for item in data:
            text = item.get('text', '').lower()
            if any(kw in text for kw in military_keywords):
                count += 1
        return count
    
    def _count_dual_use(self, data: List[Dict]) -> int:
        """Count dual-use technologies"""
        dual_use_keywords = ['autonomous', 'encryption', 'drone', 'ai', 'quantum']
        count = 0
        for item in data:
            text = item.get('text', '').lower()
            if any(kw in text for kw in dual_use_keywords):
                # Check if both civilian and military indicators present
                has_civilian = any(kw in text for kw in ['commercial', 'civilian', 'consumer'])
                has_military = any(kw in text for kw in ['military', 'defense'])
                if has_civilian or has_military:
                    count += 1
        return count
    
    def _count_wassenaar(self, data: List[Dict]) -> int:
        """Count Wassenaar-relevant technologies"""
        classifier = WassenarrClassifier()
        count = 0
        for item in data:
            classifications = classifier.classify(item.get('text', ''))
            if any(c['risk_level'] in ['MEDIUM', 'HIGH'] for c in classifications):
                count += 1
        return count
    
    def _extract_key_developments(self, data: List[Dict]) -> List[str]:
        """Extract key developments from year"""
        # Return top 3 most significant developments
        developments = []
        for item in data[:3]:
            text = item.get('text', '')
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                developments.append(sentences[0][:200])
        return developments


class EnhancedGeopoliticalAnalyzer:
    """Main analyzer combining all capabilities"""
    
    def __init__(self):
        self.wassenaar = WassenarrClassifier()
        self.verifier = FactVerifier()
        self.temporal = TemporalAnalyzer()
    
    async def analyze_single_country(
        self,
        country: str,
        domain: str,
        data: List[Dict],
        years: int = 5
    ) -> Dict:
        """Comprehensive single-country analysis"""
        
        # Temporal analysis
        timeline = self.temporal.analyze_timeline(data, years)
        
        # Wassenaar classification
        wassenaar_results = []
        for item in data:
            classifications = self.wassenaar.classify(item.get('text', ''))
            wassenaar_results.extend(classifications)
        
        # Risk assessment
        risk_profile = self._generate_risk_profile(wassenaar_results)
        
        # Fact verification
        claims = self._extract_claims(data)
        verified_claims = []
        for claim in claims[:10]:  # Verify top 10 claims
            verification = await self.verifier.verify_claim(claim, data)
            verified_claims.append(verification)
        
        return {
            'country': country,
            'domain': domain,
            'timeline': timeline,
            'risk_profile': risk_profile,
            'wassenaar_compliance': self._assess_compliance(wassenaar_results),
            'verified_developments': verified_claims,
            'military_civilian_ratio': self._calculate_ratio(timeline),
            'overall_risk': self._calculate_overall_risk(risk_profile)
        }
    
    def _generate_risk_profile(self, classifications: List[Dict]) -> Dict:
        """Generate comprehensive risk profile"""
        if not classifications:
            return {'categories': [], 'overall': 'LOW'}
        
        # Group by category
        by_category = {}
        for c in classifications:
            cat = c['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(c)
        
        # Generate profile
        categories = []
        for cat, items in by_category.items():
            avg_risk = sum(1 for i in items if i['risk_level'] == 'HIGH') / len(items)
            categories.append({
                'category': cat,
                'risk_level': 'HIGH' if avg_risk > 0.3 else 'MEDIUM' if avg_risk > 0.1 else 'LOW',
                'flagged_count': sum(1 for i in items if i['military_indicators']),
                'total_count': len(items)
            })
        
        overall = 'HIGH' if any(c['risk_level'] == 'HIGH' for c in categories) else 'MEDIUM'
        
        return {
            'categories': categories,
            'overall': overall
        }
    
    def _assess_compliance(self, classifications: List[Dict]) -> Dict:
        """Assess Wassenaar compliance"""
        total = len(classifications)
        flagged = sum(1 for c in classifications if c['risk_level'] == 'HIGH')
        regulated = sum(1 for c in classifications if c['risk_level'] in ['MEDIUM', 'HIGH'])
        
        return {
            'total_technologies': total,
            'regulated': regulated,
            'flagged': flagged,
            'compliant': regulated - flagged,
            'compliance_rate': (regulated - flagged) / regulated if regulated > 0 else 1.0
        }
    
    def _extract_claims(self, data: List[Dict]) -> List[str]:
        """Extract verifiable claims from data"""
        claims = []
        for item in data:
            text = item.get('text', '')
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                if len(sentence.split()) > 10:  # Substantial claims only
                    claims.append(sentence.strip())
        return claims
    
    def _calculate_ratio(self, timeline: List[Dict]) -> Dict:
        """Calculate military vs civilian ratio"""
        total_military = sum(y['military_linked'] for y in timeline)
        total_civilian = sum(y['civilian_projects'] for y in timeline)
        total = total_military + total_civilian
        
        return {
            'military_percentage': (total_military / total * 100) if total > 0 else 0,
            'civilian_percentage': (total_civilian / total * 100) if total > 0 else 0,
            'assessment': 'Military-focused' if total_military > total_civilian else 'Civilian-focused'
        }
    
    def _calculate_overall_risk(self, risk_profile: Dict) -> str:
        """Calculate overall geopolitical risk"""
        high_risk_count = sum(1 for c in risk_profile['categories'] if c['risk_level'] == 'HIGH')
        total_categories = len(risk_profile['categories'])
        
        if high_risk_count / total_categories > 0.4:
            return 'HIGH'
        elif high_risk_count / total_categories > 0.2:
            return 'MEDIUM'
        return 'LOW'


# Example usage
async def main():
    analyzer = EnhancedGeopoliticalAnalyzer()
    
    # Sample data
    sample_data = [
        {'text': 'Country developed advanced AI-powered autonomous drone system for surveillance in 2023'},
        {'text': 'New quantum encryption technology announced for commercial telecommunications in 2024'},
        {'text': 'Medical imaging AI system launched for civilian healthcare applications in 2022'}
    ]
    
    result = await analyzer.analyze_single_country(
        country='United States',
        domain='Artificial Intelligence',
        data=sample_data,
        years=5
    )
    
    print("Analysis complete:", result)


if __name__ == '__main__':
    asyncio.run(main())