from sqlalchemy import Column, String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, default="pending")
    file_name = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    ocr_provider = Column(String(50), default="textract")
    llm_provider = Column(String(50), default="gemini_2.5")
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class InvoiceData(Base):
    __tablename__ = "invoice_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    invoice_number = Column(String(100))
    invoice_date = Column(DateTime)
    vendor_name = Column(String(255))
    total_amount = Column(Float)
    currency = Column(String(3), default="USD")
    extraction_confidence = Column(Float)
    extraction_timestamp = Column(DateTime, server_default=func.now())
    source_file = Column(String(500))
    extracted_data = Column(JSONB)

class OCRCoordinate(Base):
    __tablename__ = "ocr_coordinates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    page_number = Column(Integer, nullable=False)
    left = Column(Integer, nullable=False)
    top = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    text = Column(Text)
    confidence = Column(Float)
    field_name = Column(String(100), nullable=True)

class ReviewAnnotation(Base):
    __tablename__ = "review_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False)
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text)
    corrected_value = Column(Text, nullable=True)
    coordinates = Column(JSONB)
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
