import io
import tempfile
from typing import Dict, List, Optional

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

from src.core.logger import logger
from src.core.settings import settings
from src.models.schemas import OCRBoundingBox
from src.services.ocr.base import BaseOCRProvider


class TesseractOCR(BaseOCRProvider):
    def __init__(self):
        self.dpi = settings.default_ocr_dpi
        self.lang = "eng"

    async def extract_text_from_pdf(
        self,
        source: bytes,
        s3_bucket: Optional[str] = None,
        s3_key: Optional[str] = None,
    ) -> Dict[int, List[OCRBoundingBox]]:
        """
        Extract text and coordinates from PDF using Tesseract OCR

        Converts PDF to images, then processes each page with Tesseract
        """
        try:
            logger.info(f"Converting PDF to images with DPI {self.dpi}")

            images = convert_from_bytes(
                source,
                dpi=self.dpi,
                fmt="png",
                thread_count=1,
            )

            pages_boxes = {}

            for page_num, image in enumerate(images, start=1):
                boxes = self._extract_from_image(image, page_num)
                pages_boxes[page_num] = boxes
                logger.info(f"Page {page_num}: Extracted {len(boxes)} text regions")

            return pages_boxes

        except Exception as e:
            logger.error(f"Error in Tesseract PDF OCR: {e}")
            raise

    async def extract_text_from_image(self, image_bytes: bytes) -> List[OCRBoundingBox]:
        """
        Extract text from single image using Tesseract
        """
        try:
            logger.info("Starting Tesseract image OCR")

            image = Image.open(io.BytesIO(image_bytes))
            return self._extract_from_image(image, 1)

        except Exception as e:
            logger.error(f"Error in Tesseract image OCR: {e}")
            raise

    def _extract_from_image(self, image, page_num: int) -> List[OCRBoundingBox]:
        """
        Extract text and coordinates from PIL Image using Tesseract
        """
        try:
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang=self.lang,
                config="--psm 6",
            )

            boxes = []

            for i in range(len(data["text"])):
                text = data["text"][i].strip()

                if not text:
                    continue

                left = int(data["left"][i])
                top = int(data["top"][i])
                width = int(data["width"][i])
                height = int(data["height"][i])
                confidence = float(data["conf"][i])

                box = OCRBoundingBox(
                    page_number=page_num,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=text,
                    confidence=confidence,
                )

                boxes.append(box)

            return boxes

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
