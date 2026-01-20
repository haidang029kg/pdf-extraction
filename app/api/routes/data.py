from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job, InvoiceData
from app.models.schemas import ProcessingJob

router = APIRouter(prefix="/api/v1", tags=["data"])

@router.get("/jobs/{job_id}/data", response_model=ProcessingJob)
async def get_job_data(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    invoice_data = db.query(InvoiceData).filter(
        InvoiceData.job_id == job_id
    ).first()
    
    extraction_result = None
    if invoice_data and invoice_data.extracted_data:
        extraction_result = invoice_data.extracted_data
    
    return ProcessingJob(
        job_id=str(job.id),
        status=job.status,
        created_at=job.created_at,
        updated_at=job.updated_at,
        file_name=job.file_name,
        file_path=job.s3_key,
        ocr_provider=job.ocr_provider,
        llm_provider=job.llm_provider,
        progress=job.progress,
        error_message=job.error_message,
        extraction_result=extraction_result
    )
