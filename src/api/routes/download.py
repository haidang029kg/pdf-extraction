from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db import get_async_session
from src.models.database import InvoiceData, Job

router = APIRouter(prefix="/api/v1", tags=["download"])


@router.get("/jobs/{job_id}/download/json")
async def download_json(job_id: str, db: Annotated[AsyncSession, Depends(get_async_session)]):
    logger.info(f"Downloading JSON for job: {job_id}")

    result = await db.execute(select(Job).filter(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed yet")

    result = await db.execute(select(InvoiceData).filter(InvoiceData.job_id == job_id))
    invoice_data = result.scalar_one_or_none()

    if not invoice_data:
        raise HTTPException(status_code=404, detail="Extracted data not found")

    response_data = {
        "invoice": invoice_data.extracted_data if invoice_data else None,
        "metadata": {
            "ocr_provider": job.ocr_provider,
            "llm_provider": job.llm_provider,
            "extraction_timestamp": invoice_data.extraction_timestamp.isoformat()
            if invoice_data.extraction_timestamp
            else None,
            "job_id": job_id,
            "file_name": job.file_name,
        },
    }

    return JSONResponse(content=response_data)


@router.get("/jobs/{job_id}/download/excel")
async def download_excel(job_id: str, db: Annotated[AsyncSession, Depends(get_async_session)]):
    raise HTTPException(status_code=501, detail="Excel export not implemented yet")
