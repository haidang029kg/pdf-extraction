from src.core.logger import logger
from src.core.settings import settings
from src.services.ocr.base import BaseOCRProvider
from src.services.ocr.tesseract import TesseractOCR
from src.services.ocr.textract import TextractOCR


def get_ocr_provider() -> BaseOCRProvider:
    """
    Factory function to get OCR provider based on configuration
    """
    if settings.use_textract_ocr:
        logger.info("Using Textract OCR provider")
        return TextractOCR()
    else:
        logger.info("Using Tesseract OCR provider")
        return TesseractOCR()
