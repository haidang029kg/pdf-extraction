import logging

from src.core.settings import settings
from src.models.database import Job
from src.services.processing import OCRProcessingService
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_pdf_task(self, job_id: str):
    import asyncio

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    sync_engine = create_engine(settings.DATABASE_URL, echo=settings.debug)
    SessionLocal = sessionmaker(bind=sync_engine)

    db = SessionLocal()
    job = None
    try:
        logger.info(f"Processing job {job_id}")
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = "processing"
        job.progress = 10
        db.commit()

        ocr_service = OCRProcessingService()

        ocr_result = asyncio.run(ocr_service.process_pdf_for_ocr(job_id, db))

        logger.info(f"OCR processing complete for job {job_id}")
        logger.info(f"  - Quality score: {ocr_result['quality_score']:.2f}")
        logger.info(f"  - Total boxes: {ocr_result['total_boxes']}")
        logger.info(f"  - Pages processed: {ocr_result['pages_processed']}")

        job.status = "completed"
        job.progress = 100
        db.commit()

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.progress = 0
            db.commit()
        raise
    finally:
        db.close()
        sync_engine.dispose()
