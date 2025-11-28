# backend/app/services/chronological_tracker.py
from typing import Dict, List
import re
from datetime import datetime
from collections import defaultdict

class ChronologicalTracker:
    """Track year-wise technology progress and developments"""
    
    def __init__(self):
        self.event_categories = {
            "funding": ["raised", "funding", "investment", "invested", "million", "billion"],
            "launch": ["launched", "released", "introduced", "unveiled", "announced"],
            "research": ["research", "study", "discovered", "found", "breakthrough"],
            "partnership": ["partnership", "collaboration", "joint venture", "agreement", "signed"],
            "acquisition": ["acquired", "acquisition", "merger", "bought", "purchased"],
            "expansion": ["expanded", "expansion", "opened", "established", "facility"],
            "patent": ["patent", "filed", "granted", "intellectual property"],
            "regulation": ["regulation", "policy", "law", "legislation", "banned", "restricted"]
        }
    
    def track_progress(self, country: str, domain: str, data: Dict, time_range: int = None) -> Dict:
        """
        Track chronological progress in technology domain
        
        Args:
            country: Country name
            domain: Technology domain
            data: Fetched data
            time_range: Years to analyze (default: all available)
        
        Returns:
            Chronological analysis with year-wise events
        """
        combined_text = " ".join(data.get("raw_text", []))
        
        # Extract events by year
        events_by_year = self._extract_events_by_year(combined_text, country, time_range)
        
        # Analyze trends
        trends = self._analyze_trends(events_by_year)
        
        # Generate timeline
        timeline = self._generate_timeline(events_by_year)
        
        # Calculate progress metrics
        metrics = self._calculate_progress_metrics(events_by_year)
        
        return {
            "timeline": timeline,
            "events_by_year": events_by_year,
            "trends": trends,
            "metrics": metrics,
            "summary": self._generate_summary(country, domain, events_by_year, trends)
        }
    
    def _extract_events_by_year(self, text: str, country: str, time_range: int) -> Dict:
        """Extract events organized by year"""
        events = defaultdict(list)
        
        current_year = datetime.now().year
        min_year = current_year - time_range if time_range else 2010
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Find years in sentence
            year_matches = re.findall(r'\b(20\d{2})\b', sentence)
            
            if not year_matches:
                continue
            
            # Check if country is mentioned
            if country.lower() not in sentence.lower():
                continue
            
            for year_str in year_matches:
                year = int(year_str)
                
                if year < min_year or year > current_year:
                    continue
                
                # Categorize event
                event_type = self._categorize_event(sentence)
                
                # Extract key information
                event_info = {
                    "type": event_type,
                    "description": sentence.strip()[:400],
                    "importance": self._assess_importance(sentence),
                    "entities": self._extract_entities(sentence)
                }
                
                events[year].append(event_info)
        
        # Sort events within each year by importance
        for year in events:
            events[year].sort(key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x["importance"], 0), reverse=True)
        
        return dict(sorted(events.items(), reverse=True))
    
    def _categorize_event(self, text: str) -> str:
        """Categorize event based on keywords"""
        text_lower = text.lower()
        
        scores = {}
        for category, keywords in self.event_categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[category] = score
        
        if not scores:
            return "general"
        
        return max(scores, key=scores.get)
    
    def _assess_importance(self, text: str) -> str:
        """Assess importance of event"""
        high_importance = ["breakthrough", "first", "world-leading", "revolutionary", "unprecedented", "billion"]
        medium_importance = ["significant", "major", "important", "launched", "announced", "million"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_importance):
            return "high"
        elif any(word in text_lower for word in medium_importance):
            return "medium"
        else:
            return "low"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities (companies, organizations, amounts)"""
        entities = []
        
        # Extract monetary amounts
        money_pattern = r'\$\s*\d+(?:\.\d+)?\s*(?:billion|million|trillion)'
        money_matches = re.findall(money_pattern, text, re.IGNORECASE)
        entities.extend(money_matches)
        
        # Extract capitalized entities (companies, organizations)
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entity_matches = re.findall(entity_pattern, text)
        
        # Filter out common words
        common_words = {'The', 'This', 'In', 'On', 'At', 'With', 'For', 'To', 'From'}
        entities.extend([e for e in entity_matches if e not in common_words][:5])
        
        return entities[:8]
    
    def _analyze_trends(self, events_by_year: Dict) -> Dict:
        """Analyze trends over time"""
        if not events_by_year:
            return {
                "activity_trend": "insufficient_data",
                "acceleration": "unknown",
                "key_periods": []
            }
        
        # Count events per year
        event_counts = {year: len(events) for year, events in events_by_year.items()}
        
        years = sorted(event_counts.keys())
        if len(years) < 2:
            return {
                "activity_trend": "insufficient_data",
                "acceleration": "unknown",
                "key_periods": []
            }
        
        # Calculate trend
        early_avg = sum(event_counts[y] for y in years[:len(years)//2]) / (len(years)//2)
        late_avg = sum(event_counts[y] for y in years[len(years)//2:]) / (len(years) - len(years)//2)
        
        if late_avg > early_avg * 1.5:
            trend = "rapidly_increasing"
        elif late_avg > early_avg * 1.1:
            trend = "increasing"
        elif late_avg < early_avg * 0.7:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Identify key periods (years with high activity)
        avg_events = sum(event_counts.values()) / len(event_counts)
        key_periods = [
            {
                "year": year,
                "events": count,
                "significance": "high" if count > avg_events * 1.5 else "notable"
            }
            for year, count in event_counts.items()
            if count > avg_events
        ]
        
        return {
            "activity_trend": trend,
            "acceleration": self._calculate_acceleration(event_counts),
            "key_periods": sorted(key_periods, key=lambda x: x["year"], reverse=True),
            "most_active_year": max(event_counts, key=event_counts.get),
            "event_counts": event_counts
        }
    
    def _calculate_acceleration(self, event_counts: Dict) -> str:
        """Calculate if activity is accelerating"""
        years = sorted(event_counts.keys())
        if len(years) < 3:
            return "unknown"
        
        recent_years = years[-3:]
        recent_avg = sum(event_counts[y] for y in recent_years) / 3
        
        earlier_years = years[:-3]
        if earlier_years:
            earlier_avg = sum(event_counts[y] for y in earlier_years) / len(earlier_years)
            
            if recent_avg > earlier_avg * 2:
                return "rapidly_accelerating"
            elif recent_avg > earlier_avg * 1.3:
                return "accelerating"
            elif recent_avg < earlier_avg * 0.7:
                return "decelerating"
        
        return "stable"
    
    def _generate_timeline(self, events_by_year: Dict) -> List[Dict]:
        """Generate formatted timeline"""
        timeline = []
        
        for year in sorted(events_by_year.keys(), reverse=True):
            events = events_by_year[year]
            
            # Categorize events by type
            by_type = defaultdict(int)
            for event in events:
                by_type[event["type"]] += 1
            
            timeline.append({
                "year": year,
                "total_events": len(events),
                "event_types": dict(by_type),
                "highlights": [e["description"] for e in events if e["importance"] == "high"][:3],
                "key_developments": [e["description"] for e in events[:5]]
            })
        
        return timeline
    
    def _calculate_progress_metrics(self, events_by_year: Dict) -> Dict:
        """Calculate overall progress metrics"""
        total_events = sum(len(events) for events in events_by_year.values())
        
        if total_events == 0:
            return {
                "total_documented_events": 0,
                "activity_level": "low",
                "development_pace": "unknown"
            }
        
        # Count by category
        category_counts = defaultdict(int)
        importance_counts = defaultdict(int)
        
        for events in events_by_year.values():
            for event in events:
                category_counts[event["type"]] += 1
                importance_counts[event["importance"]] += 1
        
        # Determine activity level
        years_active = len(events_by_year)
        avg_events_per_year = total_events / years_active if years_active > 0 else 0
        
        if avg_events_per_year > 10:
            activity_level = "very_high"
        elif avg_events_per_year > 5:
            activity_level = "high"
        elif avg_events_per_year > 2:
            activity_level = "moderate"
        else:
            activity_level = "low"
        
        return {
            "total_documented_events": total_events,
            "years_covered": years_active,
            "avg_events_per_year": round(avg_events_per_year, 1),
            "activity_level": activity_level,
            "high_importance_events": importance_counts["high"],
            "dominant_categories": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "category_breakdown": dict(category_counts)
        }
    
    def _generate_summary(self, country: str, domain: str, events_by_year: Dict, trends: Dict) -> str:
        """Generate narrative summary"""
        if not events_by_year:
            return f"Limited documented activity for {country} in {domain}."
        
        years = sorted(events_by_year.keys())
        span = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
        
        total_events = sum(len(events) for events in events_by_year.values())
        
        trend_desc = {
            "rapidly_increasing": "rapidly escalating",
            "increasing": "growing",
            "stable": "maintaining steady",
            "decreasing": "declining"
        }.get(trends["activity_trend"], "variable")
        
        return f"{country}'s {domain} sector has shown {trend_desc} activity from {span}, with {total_events} documented developments. The most active period was {trends.get('most_active_year', 'recent years')}."