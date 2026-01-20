import boto3
from botocore.config import Config
from app.config import settings
from typing import List, Dict
from app.models.schemas import OCRBoundingBox
from app.services.ocr.base import BaseOCRProvider

class TextractOCR(BaseOCRProvider):
    def __init__(self):
        config = Config(region_name=settings.aws_region)
        self.client = boto3.client(
            'textract',
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config
        )
    
    async def extract_text_from_pdf(
        self, 
        s3_bucket: str, 
        s3_key: str
    ) -> Dict[int, List[OCRBoundingBox]]:
        response = self.client.detect_document_text(
            Document={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}}
        )
        
        pages_boxes = {}
        current_page = 1
        pages_boxes[current_page] = []
        
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                geometry = block['Geometry']['Polygon']
                x_coords = [p['X'] for p in geometry]
                y_coords = [p['Y'] for p in geometry]
                
                width = int((max(x_coords) - min(x_coords)) * 2480)
                height = int((max(y_coords) - min(y_coords)) * 3508)
                left = int(min(x_coords) * 2480)
                top = int(min(y_coords) * 3508)
                
                box = OCRBoundingBox(
                    page_number=current_page,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=block['Text'],
                    confidence=float(block.get('Confidence', 0))
                )
                
                pages_boxes[current_page].append(box)
        
        return pages_boxes
    
    async def extract_text_from_image(
        self, 
        image_bytes: bytes
    ) -> List[OCRBoundingBox]:
        response = self.client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        boxes = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                geometry = block['Geometry']['Polygon']
                x_coords = [p['X'] for p in geometry]
                y_coords = [p['Y'] for p in geometry]
                
                width = int((max(x_coords) - min(x_coords)) * 2480)
                height = int((max(y_coords) - min(y_coords)) * 3508)
                left = int(min(x_coords) * 2480)
                top = int(min(y_coords) * 3508)
                
                box = OCRBoundingBox(
                    page_number=1,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=block['Text'],
                    confidence=float(block.get('Confidence', 0))
                )
                boxes.append(box)
        
        return boxes
