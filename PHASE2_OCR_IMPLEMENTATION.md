# Phase 2: Complete OCR Implementation

## Overview

Phase 2 focuses on implementing complete OCR (Optical Character Recognition) processing for both Textract and Tesseract, with coordinate tracking for human review.

## Objectives

- [ ] Implement full Textract OCR integration with coordinate extraction
- [ ] Implement Tesseract OCR as fallback option
- [ ] Add PDF to image conversion pipeline
- [ ] Extract text with bounding box coordinates
- [ ] Store OCR coordinates in database
- [ ] Handle multi-page PDFs
- [ ] Implement OCR quality scoring

## Implementation Tasks

### 1. Textract OCR Enhancement

**File:** `app/services/ocr/textract.py`

#### 1.1 Enhanced Textract Processing

```python
import boto3
from botocore.config import Config
from app.config import settings
from typing import List, Dict, Tuple
from app.models.schemas import OCRBoundingBox
from app.services.ocr.base import BaseOCRProvider
import logging

logger = logging.getLogger(__name__)

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
        """
        Extract text and coordinates from PDF using Amazon Textract
        
        Returns dictionary mapping page numbers to lists of OCRBoundingBox
        """
        try:
            # Start asynchronous text detection (better for multi-page PDFs)
            response = self.client.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}}
            )
            job_id = response['JobId']
            logger.info(f"Started Textract job: {job_id}")
            
            # Poll for job completion
            while True:
                result = self.client.get_document_text_detection(JobId=job_id)
                status = result['JobStatus']
                
                if status == 'SUCCEEDED':
                    logger.info(f"Textract job {job_id} completed")
                    return self._parse_textract_response(result)
                elif status == 'FAILED':
                    error_msg = result.get('StatusMessage', 'Unknown error')
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
        
        for block in result['Blocks']:
            if block['BlockType'] in ['LINE', 'WORD']:
                geometry = block['Geometry']['Polygon']
                
                # Extract coordinates
                x_coords = [p['X'] for p in geometry]
                y_coords = [p['Y'] for p in geometry]
                
                min_x = min(x_coords)
                max_x = max(x_coords)
                min_y = min(y_coords)
                max_y = max(y_coords)
                
                # Convert to pixel coordinates (assuming A4 at 300 DPI: 2480x3508)
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
                    text=block['Text'],
                    confidence=float(block.get('Confidence', 0))
                )
                
                pages_boxes[current_page].append(box)
            
            # Check for page break (if page metadata exists)
            if block['BlockType'] == 'PAGE':
                current_page += 1
                pages_boxes[current_page] = []
        
        return pages_boxes
    
    async def extract_text_from_image(
        self, 
        image_bytes: bytes
    ) -> List[OCRBoundingBox]:
        """
        Extract text from single image
        """
        try:
            response = self.client.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            return self._parse_image_response(response)
            
        except Exception as e:
            logger.error(f"Error in Textract image OCR: {e}")
            raise
    
    def _parse_image_response(self, response: dict) -> List[OCRBoundingBox]:
        """
        Parse Textract image response
        """
        boxes = []
        
        for block in response['Blocks']:
            if block['BlockType'] in ['LINE', 'WORD']:
                geometry = block['Geometry']['Polygon']
                x_coords = [p['X'] for p in geometry]
                y_coords = [p['Y'] for p in geometry]
                
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
                    text=block['Text'],
                    confidence=float(block.get('Confidence', 0))
                )
                
                boxes.append(box)
        
        return boxes
    
    def get_ocr_quality_score(self, boxes: List[OCRBoundingBox]) -> float:
        """
        Calculate OCR quality score based on average confidence
        """
        if not boxes:
            return 0.0
        
        avg_confidence = sum(box.confidence for box in boxes) / len(boxes)
        return avg_confidence
```

### 2. Tesseract OCR Implementation

**File:** `app/services/ocr/tesseract.py`

```python
import pytesseract
from pdf2image import convert_from_path, convert_from_bytes
from app.config import settings
from typing import List, Dict
from app.models.schemas import OCRBoundingBox
from app.services.ocr.base import BaseOCRProvider
import logging

logger = logging.getLogger(__name__)

class TesseractOCR(BaseOCRProvider):
    def __init__(self):
        self.dpi = settings.default_ocr_dpi
        self.lang = 'eng'  # Can be made configurable
    
    async def extract_text_from_pdf(
        self, 
        pdf_path: str
    ) -> Dict[int, List[OCRBoundingBox]]:
        """
        Extract text and coordinates from PDF using Tesseract OCR
        
        Converts PDF to images, then processes each page with Tesseract
        """
        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images with DPI {self.dpi}")
            images = convert_from_path(
                pdf_path, 
                dpi=self.dpi,
                fmt='png'
            )
            
            pages_boxes = {}
            
            for page_num, image in enumerate(images, start=1):
                # Extract text with coordinates from each page
                boxes = self._extract_from_image(image, page_num)
                pages_boxes[page_num] = boxes
                
                logger.info(f"Page {page_num}: Extracted {len(boxes)} text regions")
            
            return pages_boxes
            
        except Exception as e:
            logger.error(f"Error in Tesseract PDF OCR: {e}")
            raise
    
    async def extract_text_from_image(
        self, 
        image_bytes: bytes
    ) -> List[OCRBoundingBox]:
        """
        Extract text from single image using Tesseract
        """
        from PIL import Image
        
        try:
            image = Image.open(image_bytes)
            return self._extract_from_image(image, 1)
            
        except Exception as e:
            logger.error(f"Error in Tesseract image OCR: {e}")
            raise
    
    def _extract_from_image(self, image, page_num: int) -> List[OCRBoundingBox]:
        """
        Extract text and coordinates from PIL Image using Tesseract
        """
        try:
            # Use pytesseract to get data with coordinates
            data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                lang=self.lang,
                config='--psm 6'  # Assume single uniform block of text
            )
            
            boxes = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                
                # Skip empty text
                if not text:
                    continue
                
                left = data['left'][i]
                top = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                confidence = data['conf'][i]
                
                box = OCRBoundingBox(
                    page_number=page_num,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                    text=text,
                    confidence=float(confidence)
                )
                
                boxes.append(box)
            
            return boxes
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
    
    def get_ocr_quality_score(self, boxes: List[OCRBoundingBox]) -> float:
        """
        Calculate OCR quality score
        """
        if not boxes:
            return 0.0
        
        avg_confidence = sum(box.confidence for box in boxes) / len(boxes)
        return avg_confidence
```

### 3. OCR Factory Update

**File:** `app/services/ocr/factory.py`

```python
from app.services.ocr.base import BaseOCRProvider
from app.services.ocr.textract import TextractOCR
from app.services.ocr.tesseract import TesseractOCR
from app.config import settings
import logging

logger = logging.getLogger(__name__)

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
```

### 4. OCR Processing Service

**File:** `app/services/processing.py`

```python
from app.services.ocr.factory import get_ocr_provider
from app.utils.s3 import S3Service
from app.models.database import OCRCoordinate, Job
from app.db.session import SessionLocal
from typing import Dict, List
from app.models.schemas import OCRBoundingBox
import logging

logger = logging.getLogger(__name__)

class OCRProcessingService:
    def __init__(self):
        self.ocr_provider = get_ocr_provider()
        self.s3_service = S3Service()
    
    async def process_pdf_for_ocr(self, job_id: str):
        """
        Main OCR processing pipeline for a job
        
        1. Download PDF from S3
        2. Extract text and coordinates using OCR
        3. Store coordinates in database
        4. Calculate OCR quality score
        """
        db = SessionLocal()
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Download PDF from S3
            logger.info(f"Downloading PDF from S3: {job.s3_key}")
            pdf_content = self.s3_service.get_pdf(job.s3_key)
            
            # Process with OCR
            logger.info(f"Starting OCR processing with provider: {job.ocr_provider}")
            
            if job.ocr_provider == 'textract':
                ocr_results = await self.ocr_provider.extract_text_from_pdf(
                    s3_bucket=settings.s3_bucket_name,
                    s3_key=job.s3_key
                )
            else:
                # Save PDF locally for Tesseract
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(pdf_content)
                    tmp_path = tmp.name
                    
                    ocr_results = await self.ocr_provider.extract_text_from_pdf(tmp_path)
                    
                    # Clean up temp file
                    import os
                    os.unlink(tmp_path)
            
            # Store OCR coordinates in database
            logger.info(f"Storing OCR coordinates for job {job_id}")
            await self._store_ocr_coordinates(db, job_id, ocr_results)
            
            # Calculate OCR quality score
            quality_score = self.ocr_provider.get_ocr_quality_score(
                [box for page_boxes in ocr_results.values() for box in page_boxes]
            )
            
            # Update job status
            job.status = 'ocr_completed'
            job.progress = 40
            db.commit()
            
            logger.info(f"OCR processing complete for job {job_id}, quality score: {quality_score}")
            
            return {
                'job_id': job_id,
                'status': 'completed',
                'quality_score': quality_score,
                'total_boxes': sum(len(boxes) for boxes in ocr_results.values()),
                'pages_processed': len(ocr_results)
            }
            
        except Exception as e:
            logger.error(f"Error in OCR processing for job {job_id}: {e}")
            job.status = 'failed'
            job.error_message = str(e)
            job.progress = 0
            db.commit()
            raise
        finally:
            db.close()
    
    async def _store_ocr_coordinates(
        self, 
        db, 
        job_id: str, 
        ocr_results: Dict[int, List[OCRBoundingBox]]
    ):
        """
        Store OCR coordinates in database
        """
        for page_num, boxes in ocr_results.items():
            for box in boxes:
                ocr_coord = OCRCoordinate(
                    job_id=job_id,
                    page_number=page_num,
                    left=box.left,
                    top=box.top,
                    width=box.width,
                    height=box.height,
                    text=box.text,
                    confidence=box.confidence
                )
                db.add(ocr_coord)
        
        db.commit()
        logger.info(f"Stored {sum(len(boxes) for boxes in ocr_results.values())} OCR coordinates")
```

### 5. Update Celery Task

**File:** `app/workers/tasks.py`

```python
from app.workers.celery_app import celery_app
from app.services.processing import OCRProcessingService
from app.services.llm.factory import get_llm_provider
from app.models.database import Job
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_pdf_task(self, job_id: str):
    """
    Main task to process PDF
    
    Phase 2: Complete OCR processing
    Phase 3+: LLM extraction (future)
    """
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update status to processing
        job.status = "processing"
        job.progress = 5
        db.commit()
        
        # Initialize services
        ocr_service = OCRProcessingService()
        
        # Phase 2: OCR Processing
        logger.info(f"Starting OCR processing for job {job_id}")
        ocr_result = await ocr_service.process_pdf_for_ocr(job_id)
        
        # Phase 3+: LLM extraction (will be implemented in Phase 3)
        # For now, mark job as completed after OCR
        # job.status = "llm_extraction"
        # job.progress = 50
        # db.commit()
        
        # Temporary: mark as completed for Phase 2
        job.status = "completed"
        job.progress = 100
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.progress = 0
        db.commit()
        raise
    finally:
        db.close()
```

### 6. Add Dependencies to pyproject.toml

**File:** `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    
    # OCR
    "pdf2image>=1.16.3",
    "pillow>=10.2.0",
    "pytesseract>=0.3.10",
    
    # System dependencies (install separately):
    # - tesseract-ocr (OCR engine)
    # - poppler-utils (PDF to image conversion)
]
```

### 7. Update Makefile

**File:** `Makefile`

```makefile
# Add new targets for Phase 2

install-ocr-system: ## Install system OCR dependencies
	@echo "Installing system OCR dependencies..."
	@brew install tesseract poppler || \
	apt-get update && apt-get install -y tesseract-ocr poppler-utils
	@echo "✅ OCR dependencies installed"

test-ocr: ## Test OCR functionality
	@echo "Testing OCR functionality..."
	@$(UV) run python -c "
from app.services.ocr.factory import get_ocr_provider
from app.config import settings
import asyncio

async def test_ocr():
    provider = get_ocr_provider()
    print(f'OCR Provider: {type(provider).__name__}')
    
    # Test with a sample image
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='white')
    result = await provider.extract_text_from_image(img.tobytes())
    print(f'Result: {len(result)} boxes extracted')
    return result

asyncio.run(test_ocr())
"
	@echo "✅ OCR test completed"
```

## API Changes

### Update Upload Endpoint

**File:** `app/api/routes/upload.py`

Add OCR provider validation:

```python
@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    ocr_provider: str = "textract",
    llm_provider: str = "gemini_2.5",
    db: Session = Depends(get_db),
    s3: S3Service = Depends(get_s3_service)
):
    # Validate OCR provider
    valid_providers = ["textract", "tesseract"]
    if ocr_provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OCR provider. Must be one of: {valid_providers}"
        )
    
    # ... rest of the upload logic
```

## Testing

### Test OCR Processing

```bash
# Test Textract
uv run python -c "
from app.services.ocr.textract import TextractOCR
import asyncio

async def test():
    ocr = TextractOCR()
    print('Testing Textract OCR...')
    # Add your test logic

asyncio.run(test())
"

# Test Tesseract
make test-ocr
```

## Troubleshooting

### Tesseract Not Found

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

### Poppler Not Found

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils
```

### PDF to Image Conversion Fails

```bash
# Check poppler installation
pdftoppm -v

# Manually test conversion
convert -density 300 input.pdf output.png
```

### Low OCR Quality

```bash
# Increase DPI in .env
DEFAULT_OCR_DPI=600

# Try different Tesseract PSM modes
# PSM 6: Assume single uniform block of text
# PSM 3: Fully automatic page segmentation
# PSM 1: Automatic page segmentation with OSD
```

## Success Criteria

- [ ] Textract OCR successfully extracts text with coordinates
- [ ] Tesseract OCR successfully extracts text with coordinates
- [ ] OCR results stored in database
- [ ] Quality score calculation implemented
- [ ] OCR provider switching works via .env
- [ ] Multi-page PDFs handled correctly
- [ ] Error handling and logging in place
- [ ] Unit tests for OCR services
- [ ] Integration tests with sample PDFs

## Next Phase

**Phase 3: LLM Integration**
- Implement Gemini 2.5 API client
- Implement Claude 3.5 Sonnet API client
- Extract structured invoice data
- Handle multi-page PDFs with LLM

## Notes

- OCR coordinates are normalized to A4 size at 300 DPI (2480x3508 pixels)
- Quality score helps determine when to switch OCR providers
- Async processing handles multi-page PDFs efficiently
- Error handling ensures job status is updated on failure
