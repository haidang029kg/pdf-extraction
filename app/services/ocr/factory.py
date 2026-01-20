from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.textract import TextractOCR
from app.config import settings

def get_ocr_provider() -> BaseOCRProvider:
    if settings.use_textract_ocr:
        return TextractOCR()
    else:
        raise NotImplementedError("Tesseract OCR not implemented yet")
