from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ROOT_DIR: Path = Field(default=Path.cwd(), description="Project root directory")

    LOG_DIR: Path = Field(
        default_factory=lambda: Path.cwd() / "logs", description="Directory for log files"
    )
    LOG_BACKUP_COUNT: int = Field(default=30, description="Number of log backups to keep")

    app_name: str = "Freight Invoice Extractor"
    app_version: str = "1.0.0"
    debug: bool = True

    host: str = "0.0.0.0"
    port: int = 8000

    DATABASE_URL: str = "postgresql://freight_audit:freight_audit_pass@localhost:5432/freight_audit"
    DATABASE_URL_ASYNC: str = (
        "postgresql+asyncpg://freight_audit:freight_audit_pass@localhost:5432/freight_audit"
    )
    pool_size: int = 20
    max_overflow: int = 40

    redis_url: str = "redis://localhost:6379/0"

    aws_endpoint_url: str = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"

    s3_bucket_name: str = "freight-invoices"
    s3_presigned_url_expires: int = 3600

    use_textract_ocr: bool = True
    tesseract_path: str = "/usr/bin/tesseract"

    google_api_key: str
    anthropic_api_key: str
    default_llm_provider: str = "gemini_2.5"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_track_started: bool = True

    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf"]

    default_ocr_dpi: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
