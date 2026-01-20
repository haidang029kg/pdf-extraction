from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job
from app.models.schemas import StatusResponse

router = APIRouter(prefix="/api/v1", tags=["status"])

@router.get("/jobs/{job_id}/status", response_model=StatusResponse)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    stage_mapping = {
        "pending": "Waiting to start",
        "processing": "Extracting text with OCR",
        "ocr_completed": "Analyzing with LLM",
        "extraction_completed": "Generating review data",
        "review_ready": "Ready for review",
        "completed": "Processing complete",
        "failed": f"Error: {job.error_message}"
    }
    
    return StatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        current_stage=stage_mapping.get(job.status),
        error_message=job.error_message
    )
