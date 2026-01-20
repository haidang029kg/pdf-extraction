from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job, InvoiceData
import json

router = APIRouter(prefix="/api/v1", tags=["download"])

@router.get("/jobs/{job_id}/download/json")
async def download_json(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Job is not completed yet"
        )
    
    invoice_data = db.query(InvoiceData).filter(
        InvoiceData.job_id == job_id
    ).first()
    
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Extracted data not found")
    
    response_data = {
        "invoice": invoice_data.extracted_data,
        "metadata": {
            "ocr_provider": job.ocr_provider,
            "llm_provider": job.llm_provider,
            "extraction_timestamp": invoice_data.extraction_timestamp.isoformat() if invoice_data.extraction_timestamp else None,
            "job_id": job_id,
            "file_name": job.file_name
        }
    }
    
    return JSONResponse(content=response_data)

@router.get("/jobs/{job_id}/download/excel")
async def download_excel(
    job_id: str,
    db: Session = Depends(get_db)
):
    raise HTTPException(status_code=501, detail="Excel export not implemented yet")
