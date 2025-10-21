import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura
from typing import Dict, List
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.timeout = 15.0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def fetch_country_tech_data(self, country: str, domain: str) -> Dict:
        data = {
            "raw_text": [],
            "companies": [],
            "government_initiatives": [],
            "research_institutions": [],
            "news": [],
            "investments": [],
            "fetch_errors": []
        }
        
        wiki_pages = self._generate_wikipedia_pages(country, domain)
        
        logger.info(f"Fetching data for {country} in {domain} from {len(wiki_pages)} sources")
        
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            tasks = []
            for page_title, page_url in wiki_pages:
                tasks.append(self._fetch_wikipedia_page(page_url, page_title, data, client))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Task failed: {str(result)}")
        
        total_text = sum(len(text) for text in data["raw_text"])
        logger.info(f"Fetched {len(data['raw_text'])} pages with {total_text} characters for {country}")
        
        if total_text < 500:
            logger.warning(f"Very little data fetched for {country} in {domain}")
            data["fetch_errors"].append(f"Minimal data available - only {total_text} characters collected")
        
        return data
    
    def _generate_wikipedia_pages(self, country: str, domain: str) -> List[tuple]:
        pages = []
        
        domain_normalized = domain.replace(" ", "_")
        country_normalized = country.replace(" ", "_")
        
        domain_variations = {
            "artificial intelligence": ["Artificial_intelligence", "AI", "Machine_learning", "Deep_learning"],
            "renewable energy": ["Renewable_energy", "Solar_power", "Wind_power", "Clean_energy"],
            "robotics": ["Robotics", "Robot", "Automation"],
            "biotechnology": ["Biotechnology", "Biotech", "Genetic_engineering"],
            "quantum computing": ["Quantum_computing", "Quantum_computer"],
            "space technology": ["Space_technology", "Space_exploration", "Satellite"],
            "5g": ["5G", "Telecommunications", "Mobile_network"],
            "cybersecurity": ["Cybersecurity", "Computer_security", "Information_security"],
            "blockchain": ["Blockchain", "Cryptocurrency", "Distributed_ledger"],
            "nanotechnology": ["Nanotechnology", "Nanoscience"]
        }
        
        domain_key = domain.lower()
        domain_terms = domain_variations.get(domain_key, [domain_normalized])
        
        for term in domain_terms[:3]:
            pages.append((
                f"{country} {term}",
                f"https://en.wikipedia.org/wiki/{term}_in_{country_normalized}"
            ))
            pages.append((
                f"{term}",
                f"https://en.wikipedia.org/wiki/{term}"
            ))
        
        country_specific = [
            (f"{country} Science and Technology", f"https://en.wikipedia.org/wiki/Science_and_technology_in_{country_normalized}"),
            (f"{country} Technology", f"https://en.wikipedia.org/wiki/Technology_in_{country_normalized}"),
            (f"{country} Research", f"https://en.wikipedia.org/wiki/Research_in_{country_normalized}"),
            (f"{country} Economy", f"https://en.wikipedia.org/wiki/Economy_of_{country_normalized}"),
            (f"{country}", f"https://en.wikipedia.org/wiki/{country_normalized}"),
        ]
        
        pages.extend(country_specific)
        
        return pages
    
    async def _fetch_wikipedia_page(self, url: str, title: str, data: Dict, client: httpx.AsyncClient):
        try:
            logger.debug(f"Fetching: {title} from {url}")
            response = await client.get(url)
            
            if response.status_code == 200:
                content = trafilatura.extract(response.text)
                
                if content and len(content) > 200:
                    data["raw_text"].append(content)
                    logger.info(f"Successfully fetched {len(content)} chars from {title}")
                    return
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    for tag in content_div.find_all(['script', 'style', 'table', 'sup']):
                        tag.decompose()
                    
                    paragraphs = content_div.find_all('p')
                    text_parts = []
                    for p in paragraphs[:50]:
                        text = p.get_text(strip=True)
                        if len(text) > 50:
                            text_parts.append(text)
                    
                    if text_parts:
                        combined_text = ' '.join(text_parts)
                        combined_text = re.sub(r'\s+', ' ', combined_text)
                        combined_text = re.sub(r'\[.*?\]', '', combined_text)
                        
                        data["raw_text"].append(combined_text[:8000])
                        logger.info(f"Extracted {len(combined_text)} chars from {title}")
                        return
                
                logger.warning(f"No content extracted from {title}")
            elif response.status_code == 404:
                logger.debug(f"Page not found: {title}")
            else:
                logger.warning(f"HTTP {response.status_code} for {title}")
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {title}")
            data["fetch_errors"].append(f"Timeout: {title}")
        except Exception as e:
            logger.warning(f"Error fetching {title}: {str(e)}")
            data["fetch_errors"].append(f"Error with {title}: {str(e)}")
    
    def extract_entities(self, text: str, entity_type: str) -> List[str]:
        entities = []
        
        if entity_type == "companies":
            patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Technologies|Labs|Systems|Solutions)))\b',
                r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b'
            ]
        elif entity_type == "institutions":
            patterns = [
                r'\b((?:Indian\s+)?Institute\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b([A-Z][a-z]+\s+University)\b',
                r'\b([A-Z][a-z]+\s+Research\s+(?:Center|Centre|Lab|Institute))\b'
            ]
        elif entity_type == "initiatives":
            patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Mission|Initiative|Program|Strategy|Policy|Act))\b',
            ]
        else:
            return entities
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        entities = list(set(entities))
        return entities[:10]
