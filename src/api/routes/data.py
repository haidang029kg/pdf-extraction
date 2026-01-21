from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.database import InvoiceData, Job
from src.models.schemas import ProcessingJob

router = APIRouter(prefix="/api/v1", tags=["data"])


@router.get("/jobs/{job_id}/data", response_model=ProcessingJob)
async def get_job_data(job_id: str, db: Annotated[AsyncSession, Depends(get_async_session)]):
    logger.info(f"Fetching data for job: {job_id}")

    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(select(InvoiceData).filter(InvoiceData.job_id == job_id))
    invoice_data = result.scalar_one_or_none()

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
        extraction_result=extraction_result,
    )
