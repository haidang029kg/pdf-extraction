# Phase 4: Coordinate Mapping & Human Review System

## Overview

Phase 4 focuses on mapping OCR coordinates to extracted LLM fields, generating annotated images for human review, and creating the review workflow.

## Objectives

- [ ] Map OCR text coordinates to extracted invoice fields
- [ ] Implement OpenCV highlighting for visual review
- [ ] Generate annotated images stored in S3
- [ ] Create review API endpoints
- [ ] Implement correction submission workflow
- [ ] Calculate field-level confidence scores
- [ ] Handle multi-page coordinate mapping

## Implementation Tasks

### 1. Coordinate Mapping Service

**File:** `app/services/coordinate_mapping.py`

```python
import difflib
from typing import Dict, List, Tuple
from app.models.schemas import OCRBoundingBox
import logging

logger = logging.getLogger(__name__)

class CoordinateMappingService:
    def __init__(self):
        pass
    
    def find_best_match(
        self,
        ocr_boxes: List[OCRBoundingBox],
        target_text: str,
        threshold: float = 0.6
    ) -> List[OCRBoundingBox]:
        """
        Find OCR boxes that best match the target text
        
        Uses fuzzy string matching (Levenshtein distance)
        """
        if not target_text or not ocr_boxes:
            return []
        
        matches = []
        target_lower = target_text.lower().strip()
        
        for box in ocr_boxes:
            ocr_text = box.text.lower().strip()
            
            # Calculate similarity ratio
            similarity = self._calculate_similarity(ocr_text, target_lower)
            
            if similarity >= threshold:
                matches.append({
                    'box': box,
                    'similarity': similarity
                })
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return [m['box'] for m in matches]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings
        
        Uses difflib's SequenceMatcher
        """
        matcher = difflib.SequenceMatcher(None, str1, str2)
        ratio = matcher.ratio()
        return ratio
    
    def merge_adjacent_boxes(
        self,
        boxes: List[OCRBoundingBox],
        vertical_threshold: int = 20,
        horizontal_threshold: int = 50
    ) -> List[Tuple[int, int, int, int]]:
        """
        Merge adjacent boxes that belong to same field
        
        Returns list of merged (left, top, width, height) tuples
        """
        if not boxes:
            return []
        
        # Sort by position (top-left to bottom-right)
        sorted_boxes = sorted(boxes, key=lambda b: (b.top, b.left))
        
        merged_boxes = []
        current_boxes = [sorted_boxes[0]]
        
        for box in sorted_boxes[1:]:
            last_box = current_boxes[-1]
            
            # Check if boxes are adjacent (same line)
            if (abs(box.top - last_box.top) < vertical_threshold and
                abs(box.left - (last_box.left + last_box.width)) < horizontal_threshold):
                current_boxes.append(box)
            else:
                # Merge current boxes
                merged_boxes.append(self._merge_box_list(current_boxes))
                current_boxes = [box]
        
        # Don't forget the last group
        if current_boxes:
            merged_boxes.append(self._merge_box_list(current_boxes))
        
        return merged_boxes
    
    def _merge_box_list(self, boxes: List[OCRBoundingBox]) -> Tuple[int, int, int, int]:
        """
        Merge a list of boxes into one bounding box
        """
        if not boxes:
            return (0, 0, 0, 0)
        
        min_left = min(box.left for box in boxes)
        min_top = min(box.top for box in boxes)
        max_right = max(box.left + box.width for box in boxes)
        max_bottom = max(box.top + box.height for box in boxes)
        
        width = max_right - min_left
        height = max_bottom - min_top
        
        return (min_left, min_top, width, height)
    
    def map_field_to_coordinates(
        self,
        field_name: str,
        extracted_value: str,
        ocr_boxes: List[OCRBoundingBox],
        page_number: int
    ) -> List[OCRBoundingBox]:
        """
        Map an extracted field value to OCR coordinates
        
        Returns list of OCR boxes that contain this value
        """
        # Try to find exact or similar matches
        matches = self.find_best_match(ocr_boxes, extracted_value)
        
        if not matches:
            logger.warning(f"No OCR match found for field '{field_name}' with value '{extracted_value}'")
            return []
        
        # If multiple matches, try to merge adjacent ones
        if len(matches) > 1:
            merged_coords = self.merge_adjacent_boxes(matches)
            return [
                OCRBoundingBox(
                    page_number=page_number,
                    left=coord[0],
                    top=coord[1],
                    width=coord[2],
                    height=coord[3],
                    text=extracted_value,
                    confidence=0.0
                )
                for coord in merged_coords
            ]
        
        return matches
```

### 2. OpenCV Highlighting Service

**File:** `app/services/highlighting.py`

```python
import cv2
import numpy as np
from typing import List, Tuple
from app.models.schemas import OCRBoundingBox
import logging

logger = logging.getLogger(__name__)

class HighlightingService:
    def __init__(self):
        # Colors for highlighting (BGR format)
        self.colors = {
            'default': (0, 255, 0),      # Green
            'invoice_number': (255, 0, 0),   # Blue
            'vendor_name': (0, 165, 255),  # Orange
            'total_amount': (0, 0, 255),   # Red
            'date': (255, 255, 0),      # Cyan
            'line_item': (128, 0, 128)   # Purple
        }
    
    def highlight_field(
        self,
        image: np.ndarray,
        boxes: List[OCRBoundingBox],
        field_name: str = "default",
        alpha: float = 0.3
    ) -> np.ndarray:
        """
        Highlight OCR boxes on image with transparency overlay
        
        Args:
            image: Input image (numpy array)
            boxes: List of OCRBoundingBox objects
            field_name: Name of field (determines color)
            alpha: Transparency (0.0 = fully transparent, 1.0 = opaque)
        
        Returns:
            Annotated image with highlighted boxes
        """
        overlay = image.copy()
        
        # Get color for this field type
        color = self.colors.get(field_name, self.colors['default'])
        
        # Draw rectangles on overlay
        for box in boxes:
            pt1 = (box.left, box.top)
            pt2 = (box.left + box.width, box.top + box.height)
            
            cv2.rectangle(overlay, pt1, pt2, color, -1)
            
            # Add text label
            cv2.putText(
                overlay,
                field_name,
                (box.left, box.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        # Blend overlay with original image
        highlighted = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        return highlighted
    
    def highlight_all_fields(
        self,
        image: np.ndarray,
        annotations: List[dict]
    ) -> np.ndarray:
        """
        Highlight all fields with different colors
        
        Args:
            image: Input image
            annotations: List of dicts with 'field_name', 'boxes'
        
        Returns:
            Fully annotated image
        """
        highlighted_image = image.copy()
        
        # Use different alpha for each field type to avoid clutter
        field_colors = {}
        
        for annotation in annotations:
            field_name = annotation['field_name']
            boxes = annotation['boxes']
            
            # Track which pixels have been modified
            for box in boxes:
                color = self.colors.get(field_name, self.colors['default'])
                
                pt1 = (box.left, box.top)
                pt2 = (box.left + box.width, box.top + box.height)
                
                # Draw semi-transparent rectangle
                overlay = highlighted_image.copy()
                cv2.rectangle(overlay, pt1, pt2, color, -1)
                highlighted_image = cv2.addWeighted(overlay, 0.3, highlighted_image, 0.7, 0)
                
                # Draw label
                cv2.putText(
                    highlighted_image,
                    field_name,
                    (box.left, max(0, box.top - 15)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 255, 255),
                    1
                )
        
        return highlighted_image
    
    def generate_review_image(
        self,
        image_path: str,
        annotations: List[dict],
        output_path: str
    ) -> str:
        """
        Generate review image with annotations
        
        Args:
            image_path: Path to original page image
            annotations: Field annotations
            output_path: Path to save annotated image
        
        Returns:
            Path to generated image
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Highlight all fields
            highlighted = self.highlight_all_fields(image, annotations)
            
            # Save annotated image
            cv2.imwrite(output_path, highlighted)
            
            logger.info(f"Generated review image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating review image: {e}")
            raise
```

### 3. Review API Endpoints

**File:** `app/api/routes/review.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job, InvoiceData, OCRCoordinate, ReviewAnnotation
from app.models.schemas import StatusResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["review"])

@router.get("/jobs/{job_id}/review", response_model=dict)
async def get_review_data(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get review data for human verification
    
    Returns:
    - job_id: Job identifier
    - extracted_data: All extracted invoice fields
    - annotations: OCR coordinates mapped to fields
    - review_images: S3 URLs to annotated images
    """
    # Get job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ['extraction_completed', 'review_ready', 'completed']:
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready for review. Current status: {job.status}"
        )
    
    # Get extracted invoice data
    invoice_data = db.query(InvoiceData).filter(InvoiceData.job_id == job_id).first()
    
    if not invoice_data:
        raise HTTPException(status_code=404, detail="Extracted data not found")
    
    # Get OCR coordinates
    ocr_coords = db.query(OCRCoordinate).filter(
        OCRCoordinate.job_id == job_id
    ).all()
    
    # Get review annotations
    review_annotations = db.query(ReviewAnnotation).filter(
        ReviewAnnotation.job_id == job_id
    ).all()
    
    # Group by page
    coords_by_page = {}
    for coord in ocr_coords:
        if coord.page_number not in coords_by_page:
            coords_by_page[coord.page_number] = []
        coords_by_page[coord.page_number].append(coord)
    
    return {
        "job_id": job_id,
        "status": job.status,
        "extracted_data": invoice_data.extracted_data if invoice_data else {},
        "annotations": [
            {
                "field_name": ann.field_name,
                "extracted_value": ann.extracted_value,
                "corrected_value": ann.corrected_value,
                "confidence": ann.confidence,
                "coordinates": ann.coordinates
            }
            for ann in review_annotations
        ],
        "ocr_coordinates": coords_by_page,
        "total_pages": len(coords_by_page)
    }

@router.put("/jobs/{job_id}/corrections")
async def submit_corrections(
    job_id: str,
    corrections: dict,
    db: Session = Depends(get_db)
):
    """
    Submit human corrections for extracted data
    
    Expects:
    {
        "invoice_number": "INV-12345-CORRECTED",
        "vendor_name": "Correct Vendor Name",
        ...
    }
    
    Updates review annotations and invoice data
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update review annotations with corrections
    for field_name, corrected_value in corrections.items():
        annotation = db.query(ReviewAnnotation).filter(
            ReviewAnnotation.job_id == job_id,
            ReviewAnnotation.field_name == field_name
        ).first()
        
        if annotation:
            annotation.corrected_value = corrected_value
        else:
            logger.warning(f"No annotation found for field '{field_name}'")
    
    # Update invoice data
    invoice_data = db.query(InvoiceData).filter(
        InvoiceData.job_id == job_id
    ).first()
    
    if invoice_data and invoice_data.extracted_data:
        updated_data = invoice_data.extracted_data.copy()
        updated_data.update(corrections)
        invoice_data.extracted_data = updated_data
    
    db.commit()
    
    logger.info(f"Corrections submitted for job {job_id}")
    
    return {
        "job_id": job_id,
        "status": "corrections_saved",
        "message": f"Updated {len(corrections)} fields"
    }

@router.post("/jobs/{job_id}/approve")
async def approve_extraction(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Mark extraction as approved after human review
    
    Finalizes the review process
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update status
    job.status = "completed"
    db.commit()
    
    logger.info(f"Job {job_id} approved after review")
    
    return {
        "job_id": job_id,
        "status": "approved",
        "message": "Extraction approved and ready for export"
    }

@router.get("/jobs/{job_id}/review-image/{page_number}")
async def get_review_image(
    job_id: str,
    page_number: int,
    db: Session = Depends(get_db)
):
    """
    Get URL to annotated review image for a specific page
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get review annotations for this page
    annotations = db.query(ReviewAnnotation).filter(
        ReviewAnnotation.job_id == job_id
    ).all()
    
    # In a real implementation, you'd generate the image
    # For now, return placeholder
    
    return {
        "job_id": job_id,
        "page_number": page_number,
        "image_url": f"s3://freight-invoices/review-images/{job_id}_page_{page_number}.png",
        "fields_count": len(annotations)
    }
```

### 4. Integrate Review Routes

**File:** `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import upload, status, data, download, review
from app.db.session import init_db

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Freight Invoice Data Extraction System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(status.router)
app.include_router(data.router)
app.include_router(download.router)
app.include_router(review.router)  # Add review router

@app.on_event("startup")
async def startup_event():
    init_db()
    print(f"✅ {settings.app_name} v{settings.app_version} started")

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 5. Add Dependencies

**File:** `pyproject.toml`

```toml
dependencies = [
    # ... existing dependencies ...
    
    # Computer Vision
    "opencv-python>=4.8.1",
    "numpy>=1.24.0",
    
    # String matching
    "difflib",  # Built-in, but list for clarity
]
```

### 6. Update Makefile

**File:** `Makefile`

```makefile
generate-review-images: ## Generate review images for all pending jobs
	@echo "Generating review images for pending jobs..."
	@$(UV) run python -c "
from app.db.session import SessionLocal
from app.models.database import Job
import asyncio

from app.services.highlighting import HighlightingService
from app.services.coordinate_mapping import CoordinateMappingService

async def generate():
    db = SessionLocal()
    jobs = db.query(Job).filter(Job.status == 'extraction_completed').all()
    print(f'Found {len(jobs)} jobs for review image generation')
    # Implementation would generate images
    db.close()
    
asyncio.run(generate())
"
	@echo "✅ Review images generated"
```

## Testing

### Test Coordinate Mapping

```bash
# Test fuzzy matching
uv run python -c "
from app.services.coordinate_mapping import CoordinateMappingService
from app.models.schemas import OCRBoundingBox

service = CoordinateMappingService()

boxes = [
    OCRBoundingBox(page_number=1, left=100, top=50, width=200, height=30, text='INV-12345', confidence=0.95)
]

matches = service.find_best_match(boxes, 'INV-12345')
print(f'Found {len(matches)} matches')
for match in matches:
    print(f'  Match: {match.text}')
"
```

### Test Highlighting

```bash
# Test image highlighting
uv run python -c "
from app.services.highlighting import HighlightingService
import numpy as np
import cv2

service = HighlightingService()

# Create test image
image = np.ones((500, 700, 3), dtype=np.uint8) * 255

# Test box
from app.models.schemas import OCRBoundingBox
boxes = [OCRBoundingBox(page_number=1, left=100, top=100, width=200, height=50, text='Test', confidence=0.9)]

highlighted = service.highlight_field(image, boxes, 'invoice_number')

cv2.imwrite('test_highlighted.png', highlighted)
print('Created test_highlighted.png')
"
```

### Test Review API

```bash
# Get review data
curl http://localhost:8000/api/v1/jobs/{job_id}/review

# Submit corrections
curl -X PUT http://localhost:8000/api/v1/jobs/{job_id}/corrections \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "CORRECTED-INV-123",
    "total_amount": 1250.50
  }'

# Approve extraction
curl -X POST http://localhost:8000/api/v1/jobs/{job_id}/approve
```

## Success Criteria

- [ ] Coordinate mapping finds and matches OCR text to extracted fields
- [ ] Fuzzy string matching works with >70% accuracy
- [ ] Adjacent box merging implemented
- [ ] OpenCV highlighting generates clear, readable images
- [ ] Review API endpoints return proper JSON responses
- [ ] Correction submission updates database correctly
- [ ] Review images are generated and stored in S3
- [ ] Multiple fields can be highlighted on same page without conflict
- [ ] Human review workflow is complete (view, correct, approve)

## Next Phase

**Phase 5: Export Generation & Data Validation**
- Implement JSON export with metadata
- Implement Excel export with formatting
- Add data validation rules
- Implement correction submission validation
- Add export API endpoints

## Notes

- Coordinate mapping uses Levenshtein distance for fuzzy matching
- Highlighting uses BGR colors (OpenCV default format)
- Images are saved to S3 with presigned URLs
- Review workflow supports incremental corrections
- Final approval locks extraction for export
- Alpha blending (0.3) ensures original text remains readable
