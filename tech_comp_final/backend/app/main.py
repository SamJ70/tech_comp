# backend/app/main.py (COMPLETE REPLACEMENT)
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import os
from datetime import datetime
from enum import Enum

# Import enhanced services
from .services.enhanced_data_fetcher import EnhancedDataFetcher
from .services.enhanced_data_analyzer import EnhancedDataAnalyzer
from .services.enhanced_document_generator import ImprovedDocumentGenerator as EnhancedDocumentGenerator
from .services.dual_use_analyzer import DualUseAnalyzer
from .services.chronological_tracker import ChronologicalTracker

app = FastAPI(
    title="Advanced Country Tech Comparison API",
    description="AI-powered technology comparison with dual-use monitoring",
    version="3.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums for validation
class TechDomain(str, Enum):
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    RENEWABLE_ENERGY = "Renewable Energy"
    ROBOTICS = "Robotics"
    BIOTECHNOLOGY = "Biotechnology"
    QUANTUM_COMPUTING = "Quantum Computing"
    SPACE_TECHNOLOGY = "Space Technology"
    TELECOMMUNICATIONS = "5G and Telecommunications"
    CYBERSECURITY = "Cybersecurity"
    BLOCKCHAIN = "Blockchain"
    NANOTECHNOLOGY = "Nanotechnology"
    AUTONOMOUS_VEHICLES = "Autonomous Vehicles"
    FINTECH = "Financial Technology"

# Request Models
class ComparisonRequest(BaseModel):
    country1: str = Field(..., min_length=2, max_length=100)
    country2: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., min_length=2, max_length=100)
    include_charts: bool = Field(default=True)
    detail_level: str = Field(default="standard", pattern="^(basic|standard|comprehensive)$")
    time_range: Optional[int] = Field(default=None, description="Years to analyze (e.g., 5 for last 5 years)")

class SingleCountryRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., min_length=2, max_length=100)
    time_range: Optional[int] = Field(default=None, description="Years to analyze")
    include_dual_use: bool = Field(default=True, description="Include dual-use analysis")
    include_chronology: bool = Field(default=True, description="Include chronological tracking")

# In-memory cache
comparison_cache = {}
active_tasks = {}

@app.get("/")
async def root():
    return {
        "message": "Advanced Country Tech Comparison API v3.0",
        "endpoints": {
            "/compare": "POST - Compare two countries",
            "/analyze-country": "POST - Analyze single country with dual-use monitoring",
            "/domains": "GET - List available tech domains",
            "/countries": "GET - Get country suggestions",
            "/status/{task_id}": "GET - Check comparison status",
            "/download/{filename}": "GET - Download report"
        },
        "features": [
            "Multi-source data collection",
            "AI-powered analysis",
            "Dual-use technology monitoring (Wassenaar Arrangement)",
            "Chronological progress tracking",
            "Time-range filtering",
            "Military vs civilian classification",
            "Interactive visualizations",
            "Comprehensive reports"
        ]
    }

@app.get("/domains")
async def get_domains():
    """Get list of available tech domains"""
    domains = [
        {
            "id": domain.value,
            "name": domain.value,
            "description": get_domain_description(domain.value),
            "icon": get_domain_icon(domain.value),
            "dual_use_risk": get_dual_use_risk(domain.value)
        }
        for domain in TechDomain
    ]
    return {"domains": domains}

@app.get("/countries")
async def get_country_suggestions():
    """Get list of popular countries for comparison"""
    countries = [
        {"name": "United States", "code": "US", "flag": "🇺🇸"},
        {"name": "China", "code": "CN", "flag": "🇨🇳"},
        {"name": "India", "code": "IN", "flag": "🇮🇳"},
        {"name": "United Kingdom", "code": "GB", "flag": "🇬🇧"},
        {"name": "Germany", "code": "DE", "flag": "🇩🇪"},
        {"name": "Japan", "code": "JP", "flag": "🇯🇵"},
        {"name": "South Korea", "code": "KR", "flag": "🇰🇷"},
        {"name": "France", "code": "FR", "flag": "🇫🇷"},
        {"name": "Canada", "code": "CA", "flag": "🇨🇦"},
        {"name": "Israel", "code": "IL", "flag": "🇮🇱"},
        {"name": "Singapore", "code": "SG", "flag": "🇸🇬"},
        {"name": "Australia", "code": "AU", "flag": "🇦🇺"},
        {"name": "Brazil", "code": "BR", "flag": "🇧🇷"},
        {"name": "Russia", "code": "RU", "flag": "🇷🇺"},
        {"name": "Netherlands", "code": "NL", "flag": "🇳🇱"}
    ]
    return {"countries": countries}

@app.post("/compare")
async def compare_countries(request: ComparisonRequest, background_tasks: BackgroundTasks):
    """Compare two countries"""
    try:
        if request.country1.lower() == request.country2.lower():
            raise HTTPException(status_code=400, detail="Cannot compare a country with itself")
        
        task_id = f"{request.country1}_{request.country2}_{request.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        active_tasks[task_id] = {
            "status": "initializing",
            "progress": 0,
            "message": "Starting comparison...",
            "started_at": datetime.now().isoformat()
        }
        
        background_tasks.add_task(
            perform_comparison,
            task_id, request.country1, request.country2, request.domain,
            request.include_charts, request.detail_level, request.time_range
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Comparison started successfully",
            "check_status_url": f"/status/{task_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting comparison: {str(e)}")

@app.post("/analyze-country")
async def analyze_single_country(request: SingleCountryRequest, background_tasks: BackgroundTasks):
    """Analyze single country with dual-use monitoring and chronological tracking"""
    try:
        task_id = f"{request.country}_{request.domain}_single_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        active_tasks[task_id] = {
            "status": "initializing",
            "progress": 0,
            "message": f"Starting analysis of {request.country}...",
            "started_at": datetime.now().isoformat()
        }
        
        background_tasks.add_task(
            perform_single_country_analysis,
            task_id, request.country, request.domain, request.time_range,
            request.include_dual_use, request.include_chronology
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Analysis started successfully",
            "check_status_url": f"/status/{task_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")

@app.get("/status/{task_id}")
async def get_comparison_status(task_id: str):
    """Get the status of a running task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    
    if task_info["status"] == "completed" and task_id in comparison_cache:
        return {
            **task_info,
            "results": comparison_cache[task_id]
        }
    
    return task_info

@app.get("/download/{filename}")
async def download_document(filename: str):
    """Download generated comparison document"""
    filepath = f"reports/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Background task functions
async def perform_comparison(
    task_id: str, country1: str, country2: str, domain: str,
    include_charts: bool, detail_level: str, time_range: Optional[int]
):
    """Perform the actual comparison analysis"""
    try:
        active_tasks[task_id]["status"] = "fetching_data"
        active_tasks[task_id]["progress"] = 10
        active_tasks[task_id]["message"] = f"Collecting data for {country1}..."
        
        fetcher = EnhancedDataFetcher()
        analyzer = EnhancedDataAnalyzer()
        dual_use_analyzer = DualUseAnalyzer()
        chrono_tracker = ChronologicalTracker()
        doc_generator = EnhancedDocumentGenerator()
        
        # Fetch data
        country1_data = await fetcher.fetch_country_tech_data(country1, domain)
        active_tasks[task_id]["progress"] = 30
        active_tasks[task_id]["message"] = f"Collecting data for {country2}..."
        
        country2_data = await fetcher.fetch_country_tech_data(country2, domain)
        active_tasks[task_id]["progress"] = 50
        active_tasks[task_id]["message"] = "Analyzing and comparing data..."
        
        # Perform standard analysis
        analysis = analyzer.analyze_and_compare(
            country1, country2, domain,
            country1_data, country2_data,
            detail_level=detail_level
        )
        
        active_tasks[task_id]["progress"] = 65
        active_tasks[task_id]["message"] = "Performing dual-use analysis..."
        
        # Dual-use analysis for both countries
        dual_use1 = dual_use_analyzer.analyze_dual_use(country1, domain, country1_data, time_range)
        dual_use2 = dual_use_analyzer.analyze_dual_use(country2, domain, country2_data, time_range)
        
        active_tasks[task_id]["progress"] = 75
        active_tasks[task_id]["message"] = "Tracking chronological progress..."
        
        # Chronological tracking
        chrono1 = chrono_tracker.track_progress(country1, domain, country1_data, time_range)
        chrono2 = chrono_tracker.track_progress(country2, domain, country2_data, time_range)
        
        active_tasks[task_id]["progress"] = 85
        active_tasks[task_id]["message"] = "Generating report..."
        
        # Generate document
        filename = f"{country1}_vs_{country2}_{domain.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = f"reports/{filename}"
        os.makedirs("reports", exist_ok=True)
        
        # Combine all analysis
        combined_analysis = {
            **analysis,
            "dual_use_analysis": {
                country1: dual_use1,
                country2: dual_use2
            },
            "chronological_tracking": {
                country1: chrono1,
                country2: chrono2
            },
            "time_range_analyzed": time_range
        }
        
        doc_generator.generate_document(
            country1, country2, domain,
            combined_analysis, filepath,
            include_charts=include_charts
        )
        
        # Prepare results
        results = {
            "type": "comparison",
            "domain": domain,
            "countries": [country1, country2],
            "summary": analysis["summary"],
            "comparison": analysis["comparison"],
            "overall_analysis": analysis["overall_analysis"],
            "dual_use_analysis": {
                country1: dual_use1,
                country2: dual_use2
            },
            "chronological_data": {
                country1: chrono1["timeline"][:5],
                country2: chrono2["timeline"][:5]
            },
            "trends": {
                country1: chrono1["trends"],
                country2: chrono2["trends"]
            },
            "document": {
                "filename": filename,
                "download_url": f"/download/{filename}"
            },
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "detail_level": detail_level,
                "time_range": time_range,
                "sources_used": {
                    country1: len(country1_data.get("raw_text", [])),
                    country2: len(country2_data.get("raw_text", []))
                }
            }
        }
        
        comparison_cache[task_id] = results
        
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Comparison completed successfully!"
        active_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = f"Error: {str(e)}"
        active_tasks[task_id]["error"] = str(e)

async def perform_single_country_analysis(
    task_id: str, country: str, domain: str, time_range: Optional[int],
    include_dual_use: bool, include_chronology: bool
):
    """Perform single country analysis with dual-use and chronological tracking"""
    try:
        active_tasks[task_id]["status"] = "fetching_data"
        active_tasks[task_id]["progress"] = 15
        active_tasks[task_id]["message"] = f"Collecting data for {country}..."
        
        fetcher = EnhancedDataFetcher()
        dual_use_analyzer = DualUseAnalyzer()
        chrono_tracker = ChronologicalTracker()
        
        # Fetch data
        country_data = await fetcher.fetch_country_tech_data(country, domain)
        
        active_tasks[task_id]["progress"] = 40
        active_tasks[task_id]["message"] = "Analyzing dual-use compliance..."
        
        # Dual-use analysis
        dual_use_results = None
        if include_dual_use:
            dual_use_results = dual_use_analyzer.analyze_dual_use(country, domain, country_data, time_range)
        
        active_tasks[task_id]["progress"] = 65
        active_tasks[task_id]["message"] = "Tracking chronological progress..."
        
        # Chronological tracking
        chrono_results = None
        if include_chronology:
            chrono_results = chrono_tracker.track_progress(country, domain, country_data, time_range)
        
        active_tasks[task_id]["progress"] = 90
        active_tasks[task_id]["message"] = "Finalizing analysis..."
        
        # Prepare results
        results = {
            "type": "single_country",
            "country": country,
            "domain": domain,
            "time_range": time_range,
            "dual_use_analysis": dual_use_results,
            "chronological_analysis": chrono_results,
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "sources_used": len(country_data.get("raw_text", []))
            }
        }
        
        comparison_cache[task_id] = results
        
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Analysis completed successfully!"
        active_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = f"Error: {str(e)}"
        active_tasks[task_id]["error"] = str(e)

# Utility functions
def get_domain_description(domain: str) -> str:
    descriptions = {
        "Artificial Intelligence": "Machine learning, neural networks, and AI applications",
        "Renewable Energy": "Solar, wind, hydro, and clean energy technologies",
        "Robotics": "Industrial robots, automation, and robotic systems",
        "Biotechnology": "Genetic engineering, pharmaceuticals, and biotech research",
        "Quantum Computing": "Quantum processors, quantum algorithms, and applications",
        "Space Technology": "Satellites, rockets, space exploration, and applications",
        "5G and Telecommunications": "Next-gen networks, connectivity infrastructure",
        "Cybersecurity": "Information security, threat detection, and protection systems",
        "Blockchain": "Distributed ledgers, cryptocurrencies, and blockchain applications",
        "Nanotechnology": "Nanomaterials, nanoelectronics, and nanoscale engineering"
    }
    return descriptions.get(domain, "Emerging technology domain")

def get_domain_icon(domain: str) -> str:
    icons = {
        "Artificial Intelligence": "🤖",
        "Renewable Energy": "⚡",
        "Robotics": "🦾",
        "Biotechnology": "🧬",
        "Quantum Computing": "⚛️",
        "Space Technology": "🚀",
        "5G and Telecommunications": "📡",
        "Cybersecurity": "🔒",
        "Blockchain": "⛓️",
        "Nanotechnology": "🔬"
    }
    return icons.get(domain, "💡")

def get_dual_use_risk(domain: str) -> str:
    """Get dual-use risk level for domain"""
    high_risk = ["Artificial Intelligence", "Quantum Computing", "Robotics", "Cybersecurity", "Space Technology"]
    medium_risk = ["Biotechnology", "5G and Telecommunications"]
    
    if domain in high_risk:
        return "HIGH"
    elif domain in medium_risk:
        return "MEDIUM"
    else:
        return "LOW"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)