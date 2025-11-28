# backend/app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
from datetime import datetime
import uuid
import shutil
import json
from .config import REPORTS_DIR, WASSENAAR_PDF, WASSENAAR_INDEX, TIM_EXPORT, ASPI_EXPORT
from .services.enhanced_data_fetcher import EnhancedDataFetcher
from .services.enhanced_data_analyzer import EnhancedDataAnalyzer
from .services.enhanced_document_generator import ImprovedDocumentGenerator
from .services.dual_use_analyzer import DualUseAnalyzer
from .services.chronological_tracker import ChronologicalTracker
from .db import save_analysis, get_analysis, upsert_item, get_items
from .config import NEWSAPI_KEY

app = FastAPI(title="Advanced Country Tech Comparison API", version="3.1.0")


# --- Add this to backend/app/main.py after app = FastAPI(...) ---

# Static domain and country lists used by frontend
DOMAINS = [
    {"id": "Artificial Intelligence", "name": "Artificial Intelligence",
     "description": "Machine learning, neural networks, and AI applications",
     "icon": "🤖", "dual_use_risk": "HIGH"},
    {"id": "Renewable Energy", "name": "Renewable Energy",
     "description": "Solar, wind, hydro, and clean energy technologies",
     "icon": "⚡", "dual_use_risk": "LOW"},
    {"id": "Robotics", "name": "Robotics",
     "description": "Industrial robots, automation, and robotic systems",
     "icon": "🦾", "dual_use_risk": "HIGH"},
    {"id": "Biotechnology", "name": "Biotechnology",
     "description": "Genetic engineering, pharmaceuticals, and biotech research",
     "icon": "🧬", "dual_use_risk": "MEDIUM"},
    {"id": "Quantum Computing", "name": "Quantum Computing",
     "description": "Quantum processors, quantum algorithms, and applications",
     "icon": "⚛️", "dual_use_risk": "HIGH"},
    {"id": "Space Technology", "name": "Space Technology",
     "description": "Satellites, rockets, space exploration, and applications",
     "icon": "🚀", "dual_use_risk": "HIGH"},
    {"id": "5G and Telecommunications", "name": "5G and Telecommunications",
     "description": "Next-gen networks, connectivity infrastructure",
     "icon": "📡", "dual_use_risk": "MEDIUM"},
    {"id": "Cybersecurity", "name": "Cybersecurity",
     "description": "Information security, threat detection, and protection systems",
     "icon": "🔒", "dual_use_risk": "HIGH"},
    {"id": "Blockchain", "name": "Blockchain",
     "description": "Distributed ledgers, cryptocurrencies, and blockchain applications",
     "icon": "⛓️", "dual_use_risk": "LOW"},
    {"id": "Nanotechnology", "name": "Nanotechnology",
     "description": "Nanomaterials, nanoelectronics, and nanoscale engineering",
     "icon": "🔬", "dual_use_risk": "LOW"},
    {"id": "Autonomous Vehicles", "name": "Autonomous Vehicles",
     "description": "Self-driving vehicles, control systems, sensors",
     "icon": "🚗", "dual_use_risk": "HIGH"},
    {"id": "Fintech", "name": "Financial Technology",
     "description": "Payments, blockchain fintech applications, financial models",
     "icon": "💳", "dual_use_risk": "LOW"}
]

COUNTRIES = [
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

@app.get("/domains")
async def get_domains():
    """
    Return available technology domains (id, name, description, icon, dual_use_risk).
    Frontend expects { domains: [...] }.
    """
    return {"domains": DOMAINS}

@app.get("/countries")
async def get_countries():
    """
    Return popular country suggestions (name, code, flag).
    Frontend expects { countries: [...] }.
    """
    return {"countries": COUNTRIES}
# --- End block to paste ---



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory task registry mirror (persisted via db.save_analysis)
active_tasks = {}

class ComparisonRequest(BaseModel):
    country1: str = Field(..., min_length=2)
    country2: str = Field(..., min_length=2)
    domain: str = Field(..., min_length=2)
    include_charts: bool = True
    detail_level: str = Field(default="standard")
    time_range: Optional[int] = None

class SingleCountryRequest(BaseModel):
    country: str = Field(..., min_length=2)
    domain: str = Field(..., min_length=2)
    time_range: Optional[int] = None
    include_dual_use: bool = True
    include_chronology: bool = True

# instantiate services with config (newsapi from env)
fetcher = EnhancedDataFetcher(config={"newsapi_key": NEWSAPI_KEY})
analyzer = EnhancedDataAnalyzer()
dual_use_analyzer = DualUseAnalyzer()
chrono_tracker = ChronologicalTracker()
doc_generator = ImprovedDocumentGenerator()

@app.get("/")
async def root():
    return {
        "message": "Advanced Country Tech Comparison API v3.1",
        "wassenaar_loaded": os.path.exists(WASSENAAR_INDEX) or os.path.exists(WASSENAAR_PDF),
        "tim_export_present": os.path.exists(TIM_EXPORT),
        "aspi_export_present": os.path.exists(ASPI_EXPORT)
    }

@app.post("/compare")
async def compare_countries(request: ComparisonRequest, background_tasks: BackgroundTasks):
    if request.country1.lower() == request.country2.lower():
        raise HTTPException(status_code=400, detail="Cannot compare a country with itself")
    task_id = f"cmp_{uuid.uuid4().hex[:12]}"
    active_tasks[task_id] = {"status": "started", "progress": 0, "message": "Queued", "task_id": task_id, "started_at": datetime.utcnow().isoformat()}
    save_analysis(task_id, active_tasks[task_id])
    background_tasks.add_task(perform_comparison, task_id, request.dict())
    return {"task_id": task_id, "status": "started", "check": f"/status/{task_id}"}

@app.post("/analyze-country")
async def analyze_single_country(request: SingleCountryRequest, background_tasks: BackgroundTasks):
    task_id = f"single_{uuid.uuid4().hex[:12]}"
    active_tasks[task_id] = {"status": "started", "progress": 0, "message": "Queued", "task_id": task_id, "started_at": datetime.utcnow().isoformat()}
    save_analysis(task_id, active_tasks[task_id])
    background_tasks.add_task(perform_single_country_analysis, task_id, request.dict())
    return {"task_id": task_id, "status": "started", "check": f"/status/{task_id}"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    info = active_tasks.get(task_id) or get_analysis(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="Task not found")
    return info

@app.get("/download/{filename}")
async def download_document(filename: str):
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=filename)

@app.post("/upload/wassenaar")
async def upload_wassenaar(file: UploadFile = File(...)):
    dest = WASSENAAR_PDF
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # trigger reparse by deleting index
    if os.path.exists(WASSENAAR_INDEX):
        try:
            os.remove(WASSENAAR_INDEX)
        except:
            pass
    return {"status": "uploaded", "path": dest}

@app.post("/upload/tim")
async def upload_tim(file: UploadFile = File(...)):
    dest = TIM_EXPORT
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded", "path": dest}

@app.post("/upload/aspi")
async def upload_aspi(file: UploadFile = File(...)):
    dest = ASPI_EXPORT
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded", "path": dest}

# Background workers
async def perform_comparison(task_id: str, params: dict):
    try:
        active_tasks[task_id]["status"] = "fetching"
        active_tasks[task_id]["progress"] = 5
        save_analysis(task_id, active_tasks[task_id])

        country1 = params["country1"]
        country2 = params["country2"]
        domain = params["domain"]
        time_range = params.get("time_range")

        # fetch
        active_tasks[task_id]["message"] = f"Collecting data for {country1}"
        save_analysis(task_id, active_tasks[task_id])
        c1_data = fetcher.fetch_country_tech_data(country1, domain, time_range)

        active_tasks[task_id]["message"] = f"Collecting data for {country2}"
        save_analysis(task_id, active_tasks[task_id])
        c2_data = fetcher.fetch_country_tech_data(country2, domain, time_range)

        active_tasks[task_id]["progress"] = 40
        active_tasks[task_id]["message"] = "Analyzing data"
        save_analysis(task_id, active_tasks[task_id])

        analysis = analyzer.analyze_and_compare(country1, country2, domain, c1_data, c2_data, detail_level=params.get("detail_level","standard"))

        active_tasks[task_id]["progress"] = 60
        active_tasks[task_id]["message"] = "Running dual-use checks"
        save_analysis(task_id, active_tasks[task_id])

        dual1 = dual_use_analyzer.analyze_dual_use(country1, domain, c1_data, time_range)
        dual2 = dual_use_analyzer.analyze_dual_use(country2, domain, c2_data, time_range)

        active_tasks[task_id]["progress"] = 75
        active_tasks[task_id]["message"] = "Tracking chronology"
        save_analysis(task_id, active_tasks[task_id])

        chrono1 = chrono_tracker.track_progress(country1, domain, c1_data, time_range)
        chrono2 = chrono_tracker.track_progress(country2, domain, c2_data, time_range)

        active_tasks[task_id]["progress"] = 85
        active_tasks[task_id]["message"] = "Generating document"
        save_analysis(task_id, active_tasks[task_id])

        filename = f"{country1}_vs_{country2}_{domain.replace(' ','_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(REPORTS_DIR, filename)
        combined = {
            **analysis,
            "dual_use_analysis": {country1: dual1, country2: dual2},
            "chronological_tracking": {country1: chrono1, country2: chrono2},
            "time_range_analyzed": time_range,
            "metadata": {"analyzed_at": datetime.utcnow().isoformat()}
        }
        doc_generator.generate_document(country1, country2, domain, combined, filepath, include_charts=params.get("include_charts", True))

        result = {
            "type": "comparison",
            "domain": domain,
            "countries": [country1, country2],
            "summary": analysis.get("summary"),
            "comparison": analysis.get("comparison"),
            "overall_analysis": analysis.get("overall_analysis"),
            "dual_use_analysis": {country1: dual1, country2: dual2},
            "chronological_tracking": {country1: chrono1, country2: chrono2},
            "document": {"filename": filename, "path": filepath},
            "metadata": combined.get("metadata")
        }

        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Completed"
        active_tasks[task_id]["results"] = result
        save_analysis(task_id, active_tasks[task_id])

    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = str(e)
        save_analysis(task_id, active_tasks[task_id])

async def perform_single_country_analysis(task_id: str, params: dict):
    try:
        active_tasks[task_id]["status"] = "fetching"
        active_tasks[task_id]["progress"] = 10
        save_analysis(task_id, active_tasks[task_id])

        country = params["country"]
        domain = params["domain"]
        time_range = params.get("time_range")

        active_tasks[task_id]["message"] = f"Collecting data for {country}"
        save_analysis(task_id, active_tasks[task_id])
        country_data = fetcher.fetch_country_tech_data(country, domain, time_range)

        active_tasks[task_id]["progress"] = 40
        active_tasks[task_id]["message"] = "Analyzing dual-use"
        save_analysis(task_id, active_tasks[task_id])

        dual = dual_use_analyzer.analyze_dual_use(country, domain, country_data, time_range)

        active_tasks[task_id]["progress"] = 60
        active_tasks[task_id]["message"] = "Tracking chronology"
        save_analysis(task_id, active_tasks[task_id])

        chrono = chrono_tracker.track_progress(country, domain, country_data, time_range)

        active_tasks[task_id]["progress"] = 80
        active_tasks[task_id]["message"] = "Generating document"
        save_analysis(task_id, active_tasks[task_id])

        filename = f"{country}_{domain.replace(' ','_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(REPORTS_DIR, filename)
        combined = {
            "type": "single_country",
            "country": country,
            "domain": domain,
            "time_range": time_range,
            "dual_use_analysis": dual,
            "chronological_tracking": {country: chrono},
            "metadata": {"analyzed_at": datetime.utcnow().isoformat()}
        }

        doc_generator.generate_document(country, country, domain, combined, filepath, include_charts=params.get("include_charts", True))

        result = {
            "type": "single_country",
            "country": country,
            "domain": domain,
            "time_range": time_range,
            "dual_use_analysis": dual,
            "chronological_analysis": chrono,
            "document": {"filename": filename, "path": filepath},
            "metadata": combined.get("metadata")
        }

        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Completed"
        active_tasks[task_id]["results"] = result
        save_analysis(task_id, active_tasks[task_id])

    except Exception as e:
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = str(e)
        save_analysis(task_id, active_tasks[task_id])
