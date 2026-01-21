import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.database import Job
from src.models.schemas import JobStatus, UploadResponse
from src.utils.s3 import S3Service, get_s3_service
from src.workers.tasks import process_pdf_task

router = APIRouter(prefix="/api/v1", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    s3: Annotated[S3Service, Depends(get_s3_service)],
    ocr_provider: Annotated[str, Query()] = "textract",
    llm_provider: Annotated[str, Query()] = "gemini_2.5",
):
    logger.info(f"Processing upload request for file: {file.filename}")

    valid_providers = ["textract", "tesseract"]
    if ocr_provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OCR provider. Must be one of: {valid_providers}",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_content = await file.read()

    s3_key = await s3.upload_pdf(file_content, file.filename)
    logger.info(f"File uploaded to S3: {s3_key}")

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        status=JobStatus.PENDING,
        file_name=file.filename,
        s3_key=s3_key,
        ocr_provider=ocr_provider,
        llm_provider=llm_provider,
        progress=0,
    )
    db.add(job)
    await db.commit()

    process_pdf_task.delay(job_id)
    logger.info(f"Job {job_id} queued for processing")

    return UploadResponse(
        job_id=job_id, status=JobStatus.PENDING, message="File uploaded and queued for processing"
    )
