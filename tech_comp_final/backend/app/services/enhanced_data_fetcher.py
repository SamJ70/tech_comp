import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura
from typing import Dict, List
import re
import logging

logger = logging.getLogger(__name__)

class EnhancedDataFetcher:
    def __init__(self):
        self.timeout = 30.0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.max_concurrent = 5
    
    async def fetch_country_tech_data(self, country: str, domain: str) -> Dict:
        """Enhanced multi-source data collection"""
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            # Create fetch tasks
            tasks = [
                self._fetch_wikipedia_data(country, domain, client),
                self._fetch_news_data(country, domain, client),
                self._fetch_additional_sources(country, domain, client)
            ]
            
            # Execute in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_data = {
                "raw_text": [],
                "sources": [],
                "relevance_scores": [],
                "metadata": {}
            }
            
            for result in results:
                if isinstance(result, dict):
                    combined_data["raw_text"].extend(result.get("raw_text", []))
                    combined_data["sources"].extend(result.get("sources", []))
                    combined_data["relevance_scores"].extend(result.get("relevance_scores", []))
            
            logger.info(f"Fetched {len(combined_data['raw_text'])} sources for {country}")
            return combined_data
    
    async def _fetch_wikipedia_data(self, country: str, domain: str, client: httpx.AsyncClient) -> Dict:
        """Fetch from Wikipedia with improved queries"""
        data = {"raw_text": [], "sources": [], "relevance_scores": []}
        
        # Generate smart search queries
        queries = self._generate_wiki_queries(country, domain)
        
        for query in queries[:5]:  # Limit to 5 queries
            try:
                # Search Wikipedia
                search_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "opensearch",
                    "search": query,
                    "limit": 3,
                    "namespace": 0,
                    "format": "json"
                }
                
                response = await client.get(search_url, params=params)
                if response.status_code == 200:
                    search_results = response.json()
                    if len(search_results) > 3:
                        urls = search_results[3]
                        
                        # Fetch each article
                        for url in urls[:2]:  # Top 2 results per query
                            article_data = await self._fetch_article(url, country, domain, client)
                            if article_data:
                                data["raw_text"].append(article_data["text"])
                                data["sources"].append(url)
                                data["relevance_scores"].append(article_data["relevance"])
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            except Exception as e:
                logger.warning(f"Wikipedia fetch error for '{query}': {e}")
        
        return data
    
    async def _fetch_article(self, url: str, country: str, domain: str, client: httpx.AsyncClient) -> Dict:
        """Fetch and process individual article"""
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            
            # Extract text using trafilatura
            content = trafilatura.extract(response.text)
            
            if not content or len(content) < 300:
                return None
            
            # Calculate relevance
            relevance = self._calculate_relevance(content, country, domain)
            
            if relevance >= 2.0:
                return {"text": content, "relevance": relevance}
            
            return None
        
        except Exception as e:
            logger.warning(f"Article fetch error for {url}: {e}")
            return None
    
    def _generate_wiki_queries(self, country: str, domain: str) -> List[str]:
        """Generate intelligent Wikipedia search queries"""
        queries = [
            f"{country} {domain}",
            f"{domain} in {country}",
            f"{country} technology {domain}",
            f"Science and technology in {country}",
            f"{country} innovation"
        ]
        
        # Domain-specific queries
        domain_lower = domain.lower()
        if "ai" in domain_lower or "artificial intelligence" in domain_lower:
            queries.extend([
                f"{country} artificial intelligence companies",
                f"{country} machine learning research"
            ])
        elif "energy" in domain_lower:
            queries.extend([
                f"{country} renewable energy",
                f"{country} clean technology"
            ])
        
        return queries
    
    async def _fetch_news_data(self, country: str, domain: str, client: httpx.AsyncClient) -> Dict:
        """Fetch recent news (placeholder for news API integration)"""
        # In production, integrate with News API or similar service
        return {"raw_text": [], "sources": [], "relevance_scores": []}
    
    async def _fetch_additional_sources(self, country: str, domain: str, client: httpx.AsyncClient) -> Dict:
        """Fetch from additional sources (research papers, reports)"""
        # In production, integrate with Google Scholar, arXiv, etc.
        return {"raw_text": [], "sources": [], "relevance_scores": []}
    
    def _calculate_relevance(self, text: str, country: str, domain: str) -> float:
        """Enhanced relevance scoring"""
        score = 0.0
        text_lower = text.lower()
        
        # Country mentions
        country_count = text_lower.count(country.lower())
        score += min(country_count * 0.3, 2.0)
        
        # Domain keywords
        domain_terms = domain.lower().split() + self._get_domain_keywords(domain)
        domain_count = sum(text_lower.count(term) for term in domain_terms)
        score += min(domain_count * 0.2, 3.0)
        
        # Evidence keywords
        evidence_terms = [
            "research", "development", "company", "startup", "university",
            "investment", "funding", "patent", "innovation", "launched"
        ]
        evidence_count = sum(1 for term in evidence_terms if term in text_lower)
        score += min(evidence_count * 0.2, 2.0)
        
        # Recent years bonus
        for year in ["2023", "2024", "2025"]:
            if year in text:
                score += 0.5
        
        # Length penalty/bonus
        if len(text) < 500:
            score *= 0.7
        elif len(text) > 2000:
            score += 0.5
        
        return score
    
    def _get_domain_keywords(self, domain: str) -> List[str]:
        """Get related keywords for domain"""
        keywords_map = {
            "artificial intelligence": ["ai", "machine learning", "deep learning", "neural"],
            "renewable energy": ["solar", "wind", "clean energy", "sustainable"],
            "robotics": ["robot", "automation", "autonomous"],
            "biotechnology": ["biotech", "genetic", "pharmaceutical", "biology"]
        }
        
        domain_lower = domain.lower()
        for key, keywords in keywords_map.items():
            if key in domain_lower:
                return keywords
        
        return []