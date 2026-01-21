import asyncio
from typing import Dict, List

import boto3
from botocore.config import Config

from src.core.logger import logger
from src.core.settings import settings
from src.models.schemas import OCRBoundingBox
from src.services.ocr.base import BaseOCRProvider


class TextractOCR(BaseOCRProvider):
    client: any

    def __post_init__(self):
        config = Config(region_name=settings.aws_region)
        self.client = boto3.client(
            "textract",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        )

    async def extract_text_from_pdf(
        self,
        source: bytes,
        s3_bucket: str,
        s3_key: str,
    ) -> Dict[int, List[OCRBoundingBox]]:
        """
        Extract text and coordinates from PDF using Amazon Textract

        Returns dictionary mapping page numbers to lists of OCRBoundingBox
        """
        try:
            logger.info(f"Starting Textract OCR for {s3_key}")

            response = self.client.start_document_text_detection(
                DocumentLocation={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}}
            )
            job_id = response["JobId"]
            logger.info(f"Started Textract job: {job_id}")

            while True:
                result = self.client.get_document_text_detection(JobId=job_id)
                status = result["JobStatus"]

                if status == "SUCCEEDED":
                    logger.info(f"Textract job {job_id} completed")
                    return self._parse_textract_response(result)
                elif status == "FAILED":
                    error_msg = result.get("StatusMessage", "Unknown error")
                    logger.error(f"Textract job {job_id} failed: {error_msg}")
                    raise Exception(f"Textract job failed: {error_msg}")

                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error in Textract OCR: {e}")
            raise

    def _parse_textract_response(self, result: dict) -> Dict[int, List[OCRBoundingBox]]:
        """
        Parse Textract response and extract bounding boxes

        Convert Textract geometry coordinates to pixel coordinates
        """
        pages_boxes = {}
        current_page = 1
        pages_boxes[current_page] = []

        for block in result.get("Blocks", []):
            if block["BlockType"] in ["LINE", "WORD"]:
                geometry = block["Geometry"]["Polygon"]

                x_coords = [p["X"] for p in geometry]
                y_coords = [p["Y"] for p in geometry]

                min_x = min(x_coords)
                max_x = max(x_coords)
                min_y = min(y_coords)
                max_y = max(y_coords)

                left = int(min_x * 2480)
                top = int(min_y * 3508)
                width = int((max_x - min_x) * 2480)
                height = int((max_y - min_y) * 3508)

                box = OCRBoundingBox(
                    page_number=current_page,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=block["Text"],
                    confidence=float(block.get("Confidence", 0)),
                )

                pages_boxes[current_page].append(box)

            if block["BlockType"] == "PAGE":
                current_page += 1
                pages_boxes[current_page] = []

        return pages_boxes

    async def extract_text_from_image(self, image_bytes: bytes) -> List[OCRBoundingBox]:
        """
        Extract text from single image
        """
        try:
            logger.info("Starting Textract image OCR")
            response = self.client.detect_document_text(Document={"Bytes": image_bytes})
            logger.info(f"Textract detected {len(response.get('Blocks', []))} blocks")

            boxes = self._parse_image_response(response)
            return boxes

        except Exception as e:
            logger.error(f"Error in Textract image OCR: {e}")
            raise

    def _parse_image_response(self, response: dict) -> List[OCRBoundingBox]:
        """
        Parse Textract image response
        """
        boxes = []

        for block in response.get("Blocks", []):
            if block["BlockType"] in ["LINE", "WORD"]:
                geometry = block["Geometry"]["Polygon"]
                x_coords = [p["X"] for p in geometry]
                y_coords = [p["Y"] for p in geometry]

                left = int(min(x_coords) * 2480)
                top = int(min(y_coords) * 3508)
                width = int((max(x_coords) - min(x_coords)) * 2480)
                height = int((max(y_coords) - min(y_coords)) * 3508)

                box = OCRBoundingBox(
                    page_number=1,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=block["Text"],
                    confidence=float(block.get("Confidence", 0)),
                )

                boxes.append(box)

        return boxes
