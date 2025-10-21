# Country Tech Domain Comparative Intelligence Backend

An autonomous backend-only application that compares the technological progress of two countries in a given tech domain using web scraping and data analysis.

## Features

- **Autonomous Data Collection**: Automatically fetches data from open sources (Wikipedia, tech journals, news)
- **Smart Analysis**: Analyzes and compares countries across multiple parameters
- **Word Document Reports**: Generates professional, formatted Word documents with findings
- **No API Keys Required**: Uses only free and open data sources
- **FastAPI Backend**: RESTful API endpoint for easy integration

## Technology Stack

- **FastAPI**: Lightweight async web framework
- **httpx & aiohttp**: Async HTTP requests for web scraping
- **BeautifulSoup4**: HTML parsing
- **Trafilatura**: Web content extraction
- **python-docx**: Word document generation

## Installation

The dependencies are already installed in this Replit environment:
- fastapi
- uvicorn
- httpx
- beautifulsoup4
- python-docx
- trafilatura
- aiohttp

## Running the Application

Start the server with:

```bash
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

The server will be available at `http://0.0.0.0:5000`

## API Endpoints

### POST /compare

Compare two countries in a specific tech domain.

**Request Body:**
```json
{
  "country1": "India",
  "country2": "USA",
  "domain": "Artificial Intelligence"
}
```

**Response:**
```json
{
  "domain": "Artificial Intelligence",
  "countries": ["India", "USA"],
  "summary": {
    "India": "India has rapidly scaled AI initiatives...",
    "USA": "The USA maintains dominance via private sector R&D..."
  },
  "comparison": {
    "research_activity": "USA leads with higher publications",
    "government_initiatives": "India catching up via national AI strategy",
    "industry_investment": "USA far ahead due to venture funding"
  },
  "overall_analysis": "While the USA currently leads...",
  "resources": {
    "India": ["AI4Bharat", "NITI Aayog", "IIT Research Labs"],
    "USA": ["OpenAI", "Stanford AI Lab", "DARPA Projects"]
  },
  "news": [
    {
      "source": "Research Article",
      "headline": "India launches AI Mission 2025..."
    }
  ],
  "document": {
    "filename": "India_vs_USA_Artificial_Intelligence_20231021_143022.docx",
    "download_url": "/download/India_vs_USA_Artificial_Intelligence_20231021_143022.docx"
  }
}
```

### GET /download/{filename}

Download the generated Word document report.

**Example:**
```
GET /download/India_vs_USA_Artificial_Intelligence_20231021_143022.docx
```

## Example Usage

### Using cURL

```bash
curl -X POST http://0.0.0.0:5000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "country1": "India",
    "country2": "USA",
    "domain": "Artificial Intelligence"
  }'
```

### Using Python requests

```python
import requests

response = requests.post(
    "http://0.0.0.0:5000/compare",
    json={
        "country1": "India",
        "country2": "USA",
        "domain": "Artificial Intelligence"
    }
)

data = response.json()
print(data["overall_analysis"])

document_url = f"http://0.0.0.0:5000{data['document']['download_url']}"
doc_response = requests.get(document_url)
with open("report.docx", "wb") as f:
    f.write(doc_response.content)
```

## Project Structure

```
.
├── main.py                    # FastAPI application and endpoints
├── data_fetcher.py           # Web scraping and data collection
├── data_analyzer.py          # Analysis and comparison logic
├── document_generator.py     # Word document generation
├── reports/                  # Generated Word documents (auto-created)
└── README.md                 # This file
```

## How It Works

1. **Data Fetching**: The system searches Wikipedia and other open sources for information about each country in the specified tech domain
2. **Content Extraction**: Uses Trafilatura and BeautifulSoup4 to extract clean text from web pages
3. **Analysis**: Performs keyword frequency analysis, entity extraction, and pattern recognition
4. **Comparison**: Compares both countries across multiple categories (research, industry, government, investment, education, innovation)
5. **Document Generation**: Creates a professionally formatted Word document with:
   - Executive summary
   - Country-wise overviews
   - Comparative analysis tables
   - Recent developments
   - Methodology section

## Supported Tech Domains

The system works with any technology domain. Some examples:
- Artificial Intelligence
- Renewable Energy
- Robotics
- Biotechnology
- Quantum Computing
- Space Technology
- 5G and Telecommunications
- Cybersecurity
- Blockchain
- Nanotechnology

## Limitations

- **Data Sources**: Limited to publicly available, scrapable sources
- **Real-time Data**: Some information may be slightly outdated
- **Analysis Depth**: Uses statistical analysis rather than deep AI models to stay lightweight
- **Access Restrictions**: Some sources may block automated access

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://0.0.0.0:5000/docs`
- ReDoc: `http://0.0.0.0:5000/redoc`

## Notes

- Generated Word documents are saved in the `reports/` folder
- The system is designed to be lightweight and run within free-tier resources
- No external API keys or paid services are required
- Error handling ensures graceful degradation when sources are unavailable
