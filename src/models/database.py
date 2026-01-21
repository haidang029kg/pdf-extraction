import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    ocr_provider: Mapped[str] = mapped_column(String(50), default="textract")
    llm_provider: Mapped[str] = mapped_column(String(50), default="gemini_2.5")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class InvoiceData(Base):
    __tablename__ = "invoice_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(100))
    invoice_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(255))
    total_amount: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float)
    extraction_timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    source_file: Mapped[Optional[str]] = mapped_column(String(500))
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSONB)


class OCRCoordinate(Base):
    __tablename__ = "ocr_coordinates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    left: Mapped[int] = mapped_column(Integer, nullable=False)
    top: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    field_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class ReviewAnnotation(Base):
    __tablename__ = "review_annotations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_value: Mapped[Optional[str]] = mapped_column(Text)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coordinates: Mapped[Optional[dict]] = mapped_column(JSONB)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
