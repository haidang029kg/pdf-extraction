import tempfile
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.services.ocr.factory import get_ocr_provider
from src.utils.s3 import S3Service, get_s3_service
from src.models.database import Job, OCRCoordinate
from src.models.schemas import OCRBoundingBox
from src.core.logger import logger
from src.core.settings import settings


class OCRProcessingService:
    def __init__(self):
        self.ocr_provider = get_ocr_provider()
        self.s3_service = get_s3_service()

    async def process_pdf_for_ocr(self, job_id: str, db_session: Session):
        """
        Main OCR processing pipeline for a job

        1. Download PDF from S3
        2. Extract text and coordinates using OCR
        3. Store coordinates in database
        4. Calculate OCR quality score
        """
        try:
            job = db_session.execute(select(Job).filter(Job.id == job_id)).scalar_one()
            if not job:
                raise ValueError(f"Job {job_id} not found")

            logger.info(f"Downloading PDF from S3: {job.s3_key}")
            pdf_content = await self.s3_service.get_pdf(job.s3_key)

            logger.info(f"Starting OCR processing with provider: {job.ocr_provider}")

            if job.ocr_provider == "textract":
                ocr_results = await self.ocr_provider.extract_text_from_pdf(
                    source=pdf_content,
                    s3_bucket=settings.s3_bucket_name,
                    s3_key=job.s3_key,
                )
            else:
                ocr_results = await self.ocr_provider.extract_text_from_pdf(source=pdf_content)

            await self._store_ocr_coordinates(db_session, job_id, ocr_results)

            quality_score = self.ocr_provider.get_ocr_quality_score(
                [box for page_boxes in ocr_results.values() for box in page_boxes]
            )

            job.status = "ocr_completed"
            job.progress = 40
            db_session.commit()

            logger.info(
                f"OCR processing complete for job {job_id}, "
                f"quality score: {quality_score:.2f}"
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "quality_score": quality_score,
                "total_boxes": sum(len(boxes) for boxes in ocr_results.values()),
                "pages_processed": len(ocr_results),
            }

        except Exception as e:
            logger.error(f"Error in OCR processing for job {job_id}: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.progress = 0
            db_session.commit()
            raise

    async def _store_ocr_coordinates(
        self,
        db_session: Session,
        job_id: str,
        ocr_results: Dict[int, List[OCRBoundingBox]],
    ):
        """
        Store OCR coordinates in database
        """
        for page_num, boxes in ocr_results.items():
            for box in boxes:
                ocr_coord = OCRCoordinate(
                    job_id=job_id,
                    page_number=page_num,
                    left=box.left,
                    top=box.top,
                    width=box.width,
                    height=box.height,
                    text=box.text,
                    confidence=box.confidence,
                )
                db_session.add(ocr_coord)

        db_session.commit()
        logger.info(
            f"Stored {sum(len(boxes) for boxes in ocr_results.values())} "
            f"OCR coordinates"
        )
