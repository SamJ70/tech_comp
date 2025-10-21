# Country Tech Domain Comparative Intelligence Backend

## Overview

This is an autonomous backend application that compares technological progress between two countries in a specified tech domain. The system uses web scraping and data analysis to collect information from open sources (primarily Wikipedia) and generates professional Word document reports with comparative analysis. Built with FastAPI, the application provides a single RESTful API endpoint that accepts country pairs and tech domains, then autonomously fetches, analyzes, and reports on the comparative technological landscape.

## Recent Changes

**October 21, 2025**: Enhanced data collection and validation
- Improved DataFetcher to target multiple Wikipedia pages per country/domain combination
- Added domain-specific page variations (e.g., "AI" → "Artificial_intelligence", "Machine_learning", etc.)
- Implemented comprehensive logging throughout the data fetching pipeline
- Added data validation in main.py to ensure sufficient content before processing (minimum 500 characters)
- Enhanced error handling to surface failures instead of silent swallowing
- System now successfully collects 500K-1M+ characters per country for meaningful analysis
- Tested with India vs USA in Artificial Intelligence domain: generated 38KB Word document with real data

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Architecture

**Pattern**: Modular pipeline architecture with three distinct stages
- **Data Fetching Layer**: Handles asynchronous web scraping and content extraction
- **Analysis Layer**: Processes raw text data to extract insights and generate comparisons
- **Document Generation Layer**: Creates formatted Word documents from analysis results

**Rationale**: Separation of concerns allows each component to evolve independently. The pipeline design makes it easy to add new data sources or analysis methods without affecting other parts of the system.

### Web Framework

**Choice**: FastAPI with asynchronous request handling
- Single POST endpoint (`/compare`) accepts country pairs and tech domains
- Async/await pattern throughout for efficient I/O operations
- No authentication or authorization (open API design)

**Rationale**: FastAPI provides lightweight async capabilities essential for handling multiple concurrent web scraping operations. The async nature prevents blocking during slow network requests.

### Data Collection Strategy

**Approach**: Wikipedia-focused web scraping using multiple HTTP libraries
- **httpx**: Primary async HTTP client for Wikipedia API requests
- **BeautifulSoup4**: HTML parsing and content extraction
- **Trafilatura**: Advanced web content extraction and cleaning

**Data Sources**:
- Wikipedia pages generated dynamically based on country and tech domain
- No paid APIs or API keys required
- Timeout set to 15 seconds per request to prevent hanging

**Rationale**: Wikipedia provides structured, freely accessible technology information across countries and domains. The combination of httpx (async) + BeautifulSoup (parsing) + Trafilatura (extraction) creates a robust scraping pipeline that handles various HTML structures.

### Analysis Engine

**Method**: Keyword-based text analysis with predefined category matching
- Six analysis categories: research, industry, government, investment, education, innovation
- Keyword dictionaries map terms to categories
- Statistical analysis using word frequency and entity extraction
- Comparative scoring between countries

**Output Structure**:
- Country-specific summaries
- Side-by-side comparisons across parameters
- Overall analytical narrative
- Key entities and organizations identified
- Recent news highlights

**Rationale**: Keyword-based analysis works well for technology domain comparisons where specific terminology (patents, startups, funding, research) indicates progress. This approach doesn't require ML models or training data.

### Document Generation

**Format**: Microsoft Word (.docx) documents
- **python-docx**: Library for creating formatted Word documents
- Professional styling with headers, sections, bullet points
- Structured report format: Executive Summary → Country Overviews → Comparisons

**Rationale**: Word documents are universally accessible, professionally formatted, and can be easily shared, edited, or converted. The python-docx library provides programmatic control over document structure without requiring Microsoft Office.

### Error Handling Strategy

**Approach**: Graceful degradation with error logging
- Web scraping failures logged but don't crash the application
- Minimal data warnings when insufficient content is collected
- Exception handling with `asyncio.gather(return_exceptions=True)`

**Rationale**: Web scraping is inherently unreliable (sites change, networks fail). The system continues operation even when some sources fail, ensuring partial results are better than no results.

### Concurrency Model

**Pattern**: Async/await with parallel task execution
- Multiple Wikipedia pages fetched concurrently using `asyncio.gather`
- Shared HTTP client session for connection pooling
- Controlled timeout prevents indefinite waiting

**Rationale**: Tech domain comparisons require data from multiple sources per country. Async operations reduce total execution time from sequential sum to parallel maximum, improving API response times significantly.

### File System Integration

**Approach**: Local file generation with timestamp-based naming
- Word documents saved to local filesystem
- FastAPI `FileResponse` serves generated documents
- Filenames include timestamp for uniqueness

**Considerations**: 
- No database for persistence (stateless design)
- Generated files accumulate on disk (potential cleanup needed)
- File paths are not configurable (hardcoded output directory)

**Rationale**: Stateless design simplifies deployment and scaling. Each request is independent with no shared state beyond the filesystem.

## External Dependencies

### Core Web Framework
- **FastAPI**: ASGI web framework for async API endpoints
- **Uvicorn**: ASGI server for running the FastAPI application (default port: 5000)
- **Pydantic**: Data validation through FastAPI request models

### Web Scraping Stack
- **httpx**: Async HTTP client for making web requests with 15-second timeout
- **aiohttp**: Alternative async HTTP library (imported but primary use is httpx)
- **BeautifulSoup4**: HTML/XML parsing for extracting structured content
- **Trafilatura**: Specialized web content extraction and text cleaning

### Document Processing
- **python-docx**: Microsoft Word document creation and formatting

### Data Sources
- **Wikipedia**: Primary data source for technology information
  - No API authentication required
  - Dynamically constructed URLs based on country and domain
  - Free and open access

### Python Standard Library
- **asyncio**: Async programming primitives for concurrent operations
- **re**: Regular expressions for text processing
- **collections.Counter**: Word frequency analysis
- **datetime**: Timestamp generation for reports
- **logging**: Application-level logging

### Development Environment
- **Replit**: Hosting environment with pre-installed dependencies
- All dependencies pre-configured in the environment (no requirements.txt visible)