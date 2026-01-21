from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.database import Job
from src.models.schemas import StatusResponse

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/jobs/{job_id}/status", response_model=StatusResponse)
async def get_job_status(job_id: str, db: Annotated[AsyncSession, Depends(get_async_session)]):
    logger.info(f"Fetching status for job: {job_id}")

    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    stage_mapping = {
        "pending": "Waiting to start",
        "processing": "Extracting text with OCR",
        "ocr_completed": "Analyzing with LLM",
        "extraction_completed": "Generating review data",
        "review_ready": "Ready for review",
        "completed": "Processing complete",
        "failed": f"Error: {job.error_message}",
    }

    return StatusResponse(
        job_id=str(job.id),
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        current_stage=stage_mapping.get(job.status),
        error_message=job.error_message,
    )
