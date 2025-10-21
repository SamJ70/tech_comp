import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura
from typing import Dict, List, Tuple
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedDataFetcher:
    def __init__(self):
        self.timeout = 20.0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def fetch_country_tech_data(self, country: str, domain: str) -> Dict:
        """Fetch data with improved search and validation"""
        data = {
            "raw_text": [],
            "sources": [],
            "relevance_scores": [],
            "fetch_errors": []
        }
        
        logger.info(f"Fetching data for {country} in {domain}")
        
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            # Strategy 1: Search Wikipedia for relevant articles
            search_queries = self._generate_search_queries(country, domain)
            article_urls = []
            
            for query in search_queries:
                urls = await self._search_wikipedia(query, client)
                article_urls.extend(urls)
            
            # Remove duplicates
            article_urls = list(set(article_urls))[:10]
            logger.info(f"Found {len(article_urls)} unique articles for {country}")
            
            # Strategy 2: Fetch direct pages with fallback
            direct_pages = self._generate_direct_wikipedia_urls(country, domain)
            
            # Combine and fetch
            all_urls = article_urls + [url for _, url in direct_pages]
            tasks = []
            
            for url in all_urls:
                tasks.append(self._fetch_and_validate_page(url, country, domain, data, client))
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter by relevance
        filtered_data = self._filter_by_relevance(data, country, domain)
        
        total_text = sum(len(text) for text in filtered_data["raw_text"])
        logger.info(f"Collected {total_text} relevant characters for {country}")
        
        return filtered_data
    
    def _generate_search_queries(self, country: str, domain: str) -> List[str]:
        """Generate smart search queries"""
        queries = [
            f"{country} {domain}",
            f"{domain} in {country}",
            f"{country} technology {domain}",
            f"{country} innovation {domain}",
        ]
        
        # Add domain-specific queries
        domain_lower = domain.lower()
        if "ai" in domain_lower or "artificial intelligence" in domain_lower:
            queries.extend([
                f"{country} artificial intelligence companies",
                f"{country} AI research",
                f"{country} machine learning"
            ])
        elif "renewable" in domain_lower or "energy" in domain_lower:
            queries.extend([
                f"{country} solar energy",
                f"{country} wind power",
                f"{country} clean energy"
            ])
        
        return queries[:6]
    
    async def _search_wikipedia(self, query: str, client: httpx.AsyncClient) -> List[str]:
        """Use Wikipedia's search API to find relevant articles"""
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 5,
            "namespace": 0,
            "format": "json"
        }
        
        try:
            response = await client.get(search_url, params=params)
            if response.status_code == 200:
                data = response.json()
                # OpenSearch returns [query, titles, descriptions, urls]
                if len(data) > 3:
                    logger.info(f"Search '{query}' found {len(data[3])} articles")
                    return data[3]
        except Exception as e:
            logger.warning(f"Search failed for '{query}': {e}")
        
        return []
    
    def _generate_direct_wikipedia_urls(self, country: str, domain: str) -> List[Tuple[str, str]]:
        """Generate direct URLs that might exist"""
        country_norm = country.replace(" ", "_")
        pages = [
            (f"{country}", f"https://en.wikipedia.org/wiki/{country_norm}"),
            (f"{country} Economy", f"https://en.wikipedia.org/wiki/Economy_of_{country_norm}"),
            (f"{country} Science", f"https://en.wikipedia.org/wiki/Science_and_technology_in_{country_norm}"),
        ]
        return pages
    
    async def _fetch_and_validate_page(
        self, 
        url: str, 
        country: str, 
        domain: str, 
        data: Dict, 
        client: httpx.AsyncClient
    ):
        """Fetch page and validate relevance before adding"""
        try:
            response = await client.get(url)
            
            if response.status_code != 200:
                return
            
            # Extract content
            content = trafilatura.extract(response.text)
            
            if not content or len(content) < 200:
                # Fallback to BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', {'id': 'mw-content-text'})
                
                if content_div:
                    for tag in content_div.find_all(['script', 'style', 'table', 'sup']):
                        tag.decompose()
                    
                    paragraphs = content_div.find_all('p')
                    text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
                    content = ' '.join(text_parts[:100])
                    content = re.sub(r'\s+', ' ', content)
                    content = re.sub(r'\[.*?\]', '', content)
            
            if not content or len(content) < 200:
                logger.debug(f"Insufficient content from {url}")
                return
            
            # Calculate relevance
            relevance = self._calculate_relevance_score(content, country, domain)
            
            if relevance >= 2.0:  # Minimum threshold
                data["raw_text"].append(content)
                data["sources"].append(url)
                data["relevance_scores"].append(relevance)
                logger.info(f"Added content from {url} (relevance: {relevance:.2f}, length: {len(content)})")
            else:
                logger.debug(f"Low relevance ({relevance:.2f}) for {url}")
                
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            data["fetch_errors"].append(f"{url}: {str(e)}")
    
    def _calculate_relevance_score(self, text: str, country: str, domain: str) -> float:
        """Score how relevant the text is (0-10 scale)"""
        score = 0.0
        text_lower = text.lower()
        country_lower = country.lower()
        domain_lower = domain.lower()
        
        # Essential: Must mention country
        country_mentions = text_lower.count(country_lower)
        if country_mentions > 0:
            score += min(2.0 + (country_mentions * 0.1), 3.0)
        else:
            return 0.0  # Irrelevant without country mention
        
        # Essential: Must mention domain or related terms
        domain_terms = domain_lower.split() + self._get_domain_synonyms(domain)
        domain_mentions = sum(text_lower.count(term.lower()) for term in domain_terms)
        if domain_mentions > 0:
            score += min(2.0 + (domain_mentions * 0.1), 3.0)
        
        # Bonus: Specific evidence indicators
        evidence_terms = [
            "developed", "launched", "invested", "announced", "breakthrough",
            "research", "startup", "company", "university", "institute",
            "billion", "million", "patent", "innovation", "government"
        ]
        evidence_count = sum(1 for term in evidence_terms if term in text_lower)
        score += min(evidence_count * 0.2, 2.0)
        
        # Bonus: Recent years mentioned (2020-2025)
        recent_years = ["2020", "2021", "2022", "2023", "2024", "2025"]
        if any(year in text for year in recent_years):
            score += 1.0
        
        # Penalty: Too short
        if len(text) < 500:
            score *= 0.6
        elif len(text) < 1000:
            score *= 0.8
        
        return score
    
    def _get_domain_synonyms(self, domain: str) -> List[str]:
        """Get related terms for the domain"""
        synonyms_map = {
            "artificial intelligence": ["ai", "machine learning", "deep learning", "neural network"],
            "renewable energy": ["solar", "wind", "clean energy", "sustainable energy"],
            "robotics": ["robot", "automation", "autonomous"],
            "biotechnology": ["biotech", "genetic", "pharmaceutical"],
            "quantum computing": ["quantum", "qubit", "quantum computer"],
        }
        
        domain_lower = domain.lower()
        for key, synonyms in synonyms_map.items():
            if key in domain_lower:
                return synonyms
        
        return []
    
    def _filter_by_relevance(self, data: Dict, country: str, domain: str) -> Dict:
        """Keep only highly relevant content"""
        if not data["raw_text"]:
            return data
        
        # Sort by relevance score
        sorted_data = sorted(
            zip(data["raw_text"], data["sources"], data["relevance_scores"]),
            key=lambda x: x[2],
            reverse=True
        )
        
        # Keep top content
        filtered_data = {
            "raw_text": [],
            "sources": [],
            "relevance_scores": [],
            "fetch_errors": data["fetch_errors"]
        }
        
        total_chars = 0
        max_chars = 50000  # Reasonable limit
        
        for text, source, score in sorted_data:
            if score >= 2.0 and total_chars < max_chars:
                filtered_data["raw_text"].append(text)
                filtered_data["sources"].append(source)
                filtered_data["relevance_scores"].append(score)
                total_chars += len(text)
        
        avg_relevance = sum(filtered_data["relevance_scores"]) / len(filtered_data["relevance_scores"]) if filtered_data["relevance_scores"] else 0
        logger.info(f"Kept {len(filtered_data['raw_text'])} sources with avg relevance {avg_relevance:.2f}")
        
        return filtered_data