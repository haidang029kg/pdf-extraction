from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from src.models.schemas import OCRBoundingBox


class BaseOCRProvider(ABC):
    @abstractmethod
    async def extract_text_from_pdf(
        self,
        source: bytes,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
    ) -> Dict[int, List[OCRBoundingBox]]:
        """
        Extract text and coordinates from PDF

        Args:
            source: PDF content bytes
            s3_bucket: S3 bucket name (for Textract)
            s3_key: S3 object key (for Textract)

        Returns:
            Dictionary mapping page numbers to lists of OCRBoundingBox
        """
        pass

    @abstractmethod
    async def extract_text_from_image(self, image_bytes: bytes) -> List[OCRBoundingBox]:
        """
        Extract text from single image

        Args:
            image_bytes: Image bytes

        Returns:
            List of OCRBoundingBox
        """
        pass

    def get_ocr_quality_score(self, boxes: List[OCRBoundingBox]) -> float:
        """
        Calculate OCR quality score based on average confidence

        Args:
            boxes: List of OCRBoundingBox

        Returns:
            Average confidence score
        """
        if not boxes:
            return 0.0

        avg_confidence = sum(box.confidence for box in boxes) / len(boxes)
        return avg_confidence
