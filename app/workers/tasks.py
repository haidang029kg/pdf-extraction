from app.workers.celery_app import celery_app
from app.models.database import Job
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_pdf_task(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = "processing"
        job.progress = 10
        db.commit()
        
        job.status = "completed"
        job.progress = 100
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.progress = 0
        db.commit()
        raise
    finally:
        db.close()
