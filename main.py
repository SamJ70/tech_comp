from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from datetime import datetime

from data_fetcher import DataFetcher
from data_analyzer import DataAnalyzer
from document_generator import DocumentGenerator

app = FastAPI(
    title="Country Tech Domain Comparison API",
    description="Autonomous backend for comparing technological progress between countries",
    version="1.0.0"
)

class ComparisonRequest(BaseModel):
    country1: str
    country2: str
    domain: str

@app.get("/")
async def root():
    return {
        "message": "Country Tech Domain Comparison API",
        "endpoints": {
            "/compare": "POST - Compare two countries in a tech domain",
            "/docs": "GET - API documentation"
        }
    }

@app.post("/compare")
async def compare_countries(request: ComparisonRequest):
    try:
        fetcher = DataFetcher()
        analyzer = DataAnalyzer()
        doc_generator = DocumentGenerator()
        
        country1_data = await fetcher.fetch_country_tech_data(
            request.country1, 
            request.domain
        )
        
        country2_data = await fetcher.fetch_country_tech_data(
            request.country2, 
            request.domain
        )
        
        country1_text_len = sum(len(text) for text in country1_data.get("raw_text", []))
        country2_text_len = sum(len(text) for text in country2_data.get("raw_text", []))
        
        if country1_text_len < 500:
            raise HTTPException(
                status_code=503,
                detail=f"Insufficient data collected for {request.country1}. Please try again or use a different domain."
            )
        
        if country2_text_len < 500:
            raise HTTPException(
                status_code=503,
                detail=f"Insufficient data collected for {request.country2}. Please try again or use a different domain."
            )
        
        analysis = analyzer.analyze_and_compare(
            request.country1,
            request.country2,
            request.domain,
            country1_data,
            country2_data
        )
        
        filename = f"{request.country1}_vs_{request.country2}_{request.domain.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = f"reports/{filename}"
        
        os.makedirs("reports", exist_ok=True)
        
        doc_generator.generate_document(
            request.country1,
            request.country2,
            request.domain,
            analysis,
            filepath
        )
        
        return {
            "domain": request.domain,
            "countries": [request.country1, request.country2],
            "summary": analysis["summary"],
            "comparison": analysis["comparison"],
            "overall_analysis": analysis["overall_analysis"],
            "resources": analysis["resources"],
            "news": analysis["news"],
            "document": {
                "filename": filename,
                "download_url": f"/download/{filename}"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing comparison: {str(e)}")

@app.get("/download/{filename}")
async def download_document(filename: str):
    filepath = f"reports/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
