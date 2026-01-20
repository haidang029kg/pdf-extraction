from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job
from app.utils.s3 import S3Service, get_s3_service
from app.workers.tasks import process_pdf_task
from app.models.schemas import UploadResponse, JobStatus
import uuid

router = APIRouter(prefix="/api/v1", tags=["upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    ocr_provider: str = "textract",
    llm_provider: str = "gemini_2.5",
    db: Session = Depends(get_db),
    s3: S3Service = Depends(get_s3_service)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_content = await file.read()
    
    s3_key = s3.upload_pdf(file_content, file.filename)
    
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        file_name=file.filename,
        s3_key=s3_key,
        ocr_provider=ocr_provider,
        llm_provider=llm_provider,
        progress=0
    )
    db.add(job)
    db.commit()
    
    process_pdf_task.delay(job_id)
    
    return UploadResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="File uploaded and queued for processing"
    )
