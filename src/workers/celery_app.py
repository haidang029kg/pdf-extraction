from celery import Celery

from src.core.settings import settings

celery_app = Celery(
    "freight_audit_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
)
