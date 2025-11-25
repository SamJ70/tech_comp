# backend/app/main.py
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

app = FastAPI(
    title="Advanced Country Tech Comparison API",
    description="AI-powered technology comparison between countries",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
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

class ComparisonStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str

# In-memory cache for demo (use Redis in production)
comparison_cache = {}
active_tasks = {}

@app.get("/")
async def root():
    return {
        "message": "Advanced Country Tech Comparison API v2.0",
        "endpoints": {
            "/compare": "POST - Compare two countries",
            "/domains": "GET - List available tech domains",
            "/countries": "GET - Get country suggestions",
            "/status/{task_id}": "GET - Check comparison status",
            "/download/{filename}": "GET - Download report"
        },
        "features": [
            "Multi-source data collection",
            "AI-powered analysis",
            "Real-time progress updates",
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
            "icon": get_domain_icon(domain.value)
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
    """
    Start a country comparison analysis
    Returns immediately with task_id for status tracking
    """
    try:
        # Validate inputs
        if request.country1.lower() == request.country2.lower():
            raise HTTPException(status_code=400, detail="Cannot compare a country with itself")
        
        # Generate task ID
        task_id = f"{request.country1}_{request.country2}_{request.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize task status
        active_tasks[task_id] = {
            "status": "initializing",
            "progress": 0,
            "message": "Starting comparison...",
            "started_at": datetime.now().isoformat()
        }
        
        # Run comparison in background
        background_tasks.add_task(
            perform_comparison,
            task_id,
            request.country1,
            request.country2,
            request.domain,
            request.include_charts,
            request.detail_level
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Comparison started successfully",
            "check_status_url": f"/status/{task_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting comparison: {str(e)}")

@app.get("/status/{task_id}")
async def get_comparison_status(task_id: str):
    """Get the status of a running comparison"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = active_tasks[task_id]
    
    # If completed, include results
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

@app.get("/history")
async def get_comparison_history(limit: int = 10):
    """Get recent comparisons"""
    history = sorted(
        [
            {
                "task_id": task_id,
                **task_info,
                "has_results": task_id in comparison_cache
            }
            for task_id, task_info in active_tasks.items()
            if task_info["status"] == "completed"
        ],
        key=lambda x: x.get("completed_at", ""),
        reverse=True
    )[:limit]
    
    return {"history": history}

# Background task function
async def perform_comparison(
    task_id: str,
    country1: str,
    country2: str,
    domain: str,
    include_charts: bool,
    detail_level: str
):
    """Perform the actual comparison analysis"""
    try:
        # Update status
        active_tasks[task_id]["status"] = "fetching_data"
        active_tasks[task_id]["progress"] = 10
        active_tasks[task_id]["message"] = f"Collecting data for {country1}..."
        
        # Initialize services
        fetcher = EnhancedDataFetcher()
        analyzer = EnhancedDataAnalyzer()
        doc_generator = EnhancedDocumentGenerator()
        
        # Fetch data for country 1
        country1_data = await fetcher.fetch_country_tech_data(country1, domain)
        active_tasks[task_id]["progress"] = 30
        active_tasks[task_id]["message"] = f"Collecting data for {country2}..."
        
        # Fetch data for country 2
        country2_data = await fetcher.fetch_country_tech_data(country2, domain)
        active_tasks[task_id]["progress"] = 50
        active_tasks[task_id]["message"] = "Analyzing and comparing data..."
        
        # Perform analysis
        analysis = analyzer.analyze_and_compare(
            country1, country2, domain,
            country1_data, country2_data,
            detail_level=detail_level
        )
        active_tasks[task_id]["progress"] = 80
        active_tasks[task_id]["message"] = "Generating report..."
        
        # Generate document
        filename = f"{country1}_vs_{country2}_{domain.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = f"reports/{filename}"
        os.makedirs("reports", exist_ok=True)
        
        doc_generator.generate_document(
            country1, country2, domain,
            analysis, filepath,
            include_charts=include_charts
        )
        
        # Prepare results
        results = {
            "domain": domain,
            "countries": [country1, country2],
            "summary": analysis["summary"],
            "metrics": analysis.get("concrete_metrics", {}),
            "comparison": analysis["comparison"],
            "overall_analysis": analysis["overall_analysis"],
            "charts_data": analysis.get("charts_data", {}),
            "key_findings": analysis.get("key_findings", []),
            "recommendations": analysis.get("recommendations", []),
            "data_quality": analysis.get("data_quality", {}),
            "document": {
                "filename": filename,
                "download_url": f"/download/{filename}"
            },
            "metadata": {
                "analyzed_at": datetime.now().isoformat(),
                "detail_level": detail_level,
                "sources_used": {
                    country1: len(country1_data.get("raw_text", [])),
                    country2: len(country2_data.get("raw_text", []))
                }
            }
        }
        
        # Cache results
        comparison_cache[task_id] = results
        
        # Update status
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Comparison completed successfully!"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)