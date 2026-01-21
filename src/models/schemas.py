from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    OCR_COMPLETED = "ocr_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    REVIEW_READY = "review_ready"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRBoundingBox(BaseModel):
    page_number: int
    left: int
    top: int
    width: int
    height: int
    text: str
    confidence: float


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    total: float
    service_type: Optional[str] = None


class TaxItem(BaseModel):
    tax_type: str
    rate: float
    amount: float


class SurchargeItem(BaseModel):
    charge_type: str
    amount: float


class FreightInvoice(BaseModel):
    invoice_number: str
    invoice_date: date
    vendor_name: str
    vendor_address: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    customer_tax_id: Optional[str] = None
    currency: str = "USD"
    total_amount: float
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None
    bill_of_lading: Optional[str] = None
    shipment_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    subtotal: Optional[float] = None
    taxes: List[TaxItem] = []
    surcharges: List[SurchargeItem] = []
    line_items: List[LineItem] = []
    extraction_confidence: float
    extraction_timestamp: datetime
    source_file: str


class ExtractionAnnotation(BaseModel):
    field_name: str
    extracted_value: str
    coordinates: List[OCRBoundingBox]
    confidence: float


class ProcessingJob(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    file_name: str
    file_path: str
    ocr_provider: str = "textract"
    llm_provider: str = "gemini_2.5"
    progress: int = 0
    error_message: Optional[str] = None
    extraction_result: Optional[FreightInvoice] = None
    review_annotations: Optional[List[ExtractionAnnotation]] = None


class JobCreate(BaseModel):
    file_name: str
    ocr_provider: Optional[str] = "textract"
    llm_provider: Optional[str] = "gemini_2.5"


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    created_at: datetime
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
