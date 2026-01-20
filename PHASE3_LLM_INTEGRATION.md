# Phase 3: LLM Integration

## Overview

Phase 3 focuses on integrating LLM providers (Google Gemini 2.5 and Anthropic Claude 3.5 Sonnet) to extract structured invoice data from OCR text.

## Objectives

- [ ] Implement Gemini 2.5 API client with vision support
- [ ] Implement Claude 3.5 Sonnet API client with vision support
- [ ] Create LLM factory for provider switching
- [ ] Extract structured invoice data from OCR text
- [ ] Handle multi-page PDFs with context
- [ ] Implement response parsing with confidence scores
- [ ] Add retry logic for LLM API failures

## Implementation Tasks

### 1. Gemini 2.5 Implementation

**File:** `app/services/llm/gemini.py`

```python
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from app.config import settings
from typing import Dict, Any
from app.services.llm.base import BaseLLMProvider
import logging
import json

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = settings.google_api_key
        
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(settings.default_llm_provider)
        
        # Configure safety settings (allow business documents)
        self.safety_settings = [
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_NONE
            },
        ]
    
    async def extract_invoice_data(
        self, 
        ocr_text: str, 
        page_images: Dict[int, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured invoice data using Gemini 2.5
        
        Args:
            ocr_text: OCR text from PDF
            page_images: Dictionary mapping page numbers to image data
        
        Returns:
            Dictionary with extracted invoice fields
        """
        try:
            # Create prompt for freight invoice extraction
            prompt = self._create_extraction_prompt(ocr_text)
            
            # Prepare content (text + images)
            content_parts = [prompt]
            
            # Add images if available (vision capabilities)
            if page_images:
                for page_num, image_data in sorted(page_images.items()):
                    # Convert image data to appropriate format
                    if hasattr(image_data, 'read'):
                        # File object
                        content_parts.append(
                            genai.types.Part.from_bytes(
                                data=image_data.read(),
                                mime_type="image/png"
                            )
                        )
                    else:
                        # Bytes
                        content_parts.append(
                            genai.types.Part.from_bytes(
                                data=image_data,
                                mime_type="image/png"
                            )
                        )
            
            logger.info(f"Sending request to Gemini with {len(content_parts)} parts")
            
            # Generate content with structured output
            response = await asyncio.to_thread(
                self.client.generate_content,
                content_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more deterministic output
                    max_output_tokens=4096,
                    response_mime_type="application/json"  # Request JSON output
                )
            )
            
            # Parse response
            result_text = response.text
            logger.info(f"Gemini response length: {len(result_text)}")
            
            # Parse JSON response
            try:
                extracted_data = json.loads(result_text)
                logger.info(f"Successfully parsed invoice data with {len(extracted_data)} fields")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                # Fallback: try to extract from text
                return self._extract_from_text(result_text)
                
        except Exception as e:
            logger.error(f"Error in Gemini extraction: {e}")
            raise
    
    def _create_extraction_prompt(self, ocr_text: str) -> str:
        """
        Create detailed prompt for freight invoice extraction
        """
        return f"""You are an expert at extracting structured data from freight invoices.

Please extract the following information from the OCR text below and return it as JSON:

OCR Text:
{ocr_text}

Extract these fields and return as JSON with this exact structure:
{{
    "invoice_number": "string",
    "invoice_date": "YYYY-MM-DD",
    "vendor_name": "string",
    "vendor_address": "string or null",
    "vendor_tax_id": "string or null",
    "customer_name": "string or null",
    "customer_address": "string or null",
    "customer_tax_id": "string or null",
    "currency": "string (default: USD)",
    "total_amount": "number",
    "payment_terms": "string or null",
    "due_date": "YYYY-MM-DD or null",
    "bill_of_lading": "string or null",
    "shipment_id": "string or null",
    "origin": "string or null",
    "destination": "string or null",
    "weight": "number or null",
    "weight_unit": "string (e.g., KG, LB)",
    "subtotal": "number or null",
    "taxes": [
        {{"tax_type": "string", "rate": "number", "amount": "number"}}
    ],
    "surcharges": [
        {{"charge_type": "string", "amount": "number"}}
    ],
    "line_items": [
        {{
            "description": "string",
            "quantity": "number or null",
            "unit": "string or null",
            "unit_price": "number or null",
            "total": "number",
            "service_type": "string or null"
        }}
    ],
    "extraction_confidence": "number between 0 and 1",
    "extraction_timestamp": "YYYY-MM-DDTHH:MM:SS"
}}

Requirements:
- Return ONLY valid JSON, no additional text
- If a field cannot be found, use null
- Format dates as YYYY-MM-DD
- Use decimal format for currency amounts
- extraction_confidence should be your confidence in the extraction (0-1)
- extraction_timestamp should be current UTC time

Return the JSON structure above with the extracted values."""
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Fallback method to extract data from unstructured text
        """
        import re
        from datetime import datetime, timezone
        
        result = {
            "invoice_number": None,
            "invoice_date": None,
            "vendor_name": None,
            "total_amount": None,
            "line_items": [],
            "extraction_confidence": 0.5,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Extract invoice number (pattern: INV-#### or Invoice ####)
        invoice_match = re.search(r'(?:INV|Invoice)[\s-]*:?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if invoice_match:
            result['invoice_number'] = invoice_match.group(1)
        
        # Extract date (pattern: MM/DD/YYYY or YYYY-MM-DD)
        date_match = re.search(r'\b(0[1-9]|1[0-2])[-/](0[1-9]|[12])[/-/](19|20)\d{2}\b', text)
        if date_match:
            result['invoice_date'] = date_match.group(0)
        
        # Extract vendor name (usually at the beginning)
        lines = text.split('\n')
        if lines:
            result['vendor_name'] = lines[0].strip() if lines[0].strip() else None
        
        return result
```

### 2. Claude 3.5 Sonnet Implementation

**File:** `app/services/llm/claude.py`

```python
import anthropic
from anthropic import Anthropic
from app.config import settings
from typing import Dict, Any
from app.services.llm.base import BaseLLMProvider
import logging
import json
import base64

logger = logging.getLogger(__name__)

class ClaudeProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None):
        if not api_key:
            api_key = settings.anthropic_api_key
        
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def extract_invoice_data(
        self, 
        ocr_text: str, 
        page_images: Dict[int, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract structured invoice data using Claude 3.5 Sonnet
        
        Args:
            ocr_text: OCR text from PDF
            page_images: Dictionary mapping page numbers to image data (optional)
        
        Returns:
            Dictionary with extracted invoice fields
        """
        try:
            # Create prompt
            prompt = self._create_extraction_prompt(ocr_text)
            
            # Prepare content
            content = [{"type": "text", "text": prompt}]
            
            # Add images if available
            if page_images:
                for page_num, image_data in sorted(page_images.items()):
                    # Convert image to base64
                    if hasattr(image_data, 'read'):
                        img_bytes = image_data.read()
                    else:
                        img_bytes = image_data
                    
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    })
            
            logger.info(f"Sending request to Claude with {len(content)} parts")
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": content}],
                system="You are an expert at extracting structured data from freight invoices. Always return valid JSON.",
                timeout=60
            )
            
            # Extract text from response
            result_text = message.content[0].text
            logger.info(f"Claude response length: {len(result_text)}")
            
            # Parse JSON response
            try:
                # Claude might return JSON in markdown code blocks
                json_match = re.search(r'```json\n(.*?)\n```', result_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group(1))
                else:
                    extracted_data = json.loads(result_text)
                
                logger.info(f"Successfully parsed invoice data with {len(extracted_data)} fields")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude response as JSON: {e}")
                return self._extract_from_text(result_text)
                
        except Exception as e:
            logger.error(f"Error in Claude extraction: {e}")
            raise
    
    def _create_extraction_prompt(self, ocr_text: str) -> str:
        """
        Create prompt for Claude (similar to Gemini but optimized for Claude)
        """
        return f"""Extract structured data from this freight invoice OCR text and return as JSON.

OCR Text:
{ocr_text}

Return JSON with this structure:
{{
    "invoice_number": "string",
    "invoice_date": "YYYY-MM-DD",
    "vendor_name": "string",
    "vendor_address": "string or null",
    "total_amount": "number",
    "bill_of_lading": "string or null",
    "shipment_id": "string or null",
    "origin": "string or null",
    "destination": "string or null",
    "weight": "number or null",
    "weight_unit": "string",
    "line_items": [
        {{"description": "string", "total": "number", "service_type": "string or null"}
    ],
    "surcharges": [
        {{"charge_type": "string", "amount": "number"}}
    ],
    "extraction_confidence": "number (0-1)"
}}

Requirements:
- Return ONLY valid JSON
- Format currency as decimal numbers
- Current UTC timestamp for extraction_timestamp"""
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Fallback extraction from unstructured text
        """
        import re
        from datetime import datetime, timezone
        
        result = {
            "invoice_number": None,
            "invoice_date": None,
            "vendor_name": None,
            "total_amount": None,
            "line_items": [],
            "extraction_confidence": 0.6,
            "extraction_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Similar to Gemini fallback
        invoice_match = re.search(r'(?:INV|Invoice)[\s-]*:?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if invoice_match:
            result['invoice_number'] = invoice_match.group(1)
        
        return result
```

### 3. LLM Factory

**File:** `app/services/llm/factory.py`

```python
from app.services.llm.base import BaseLLMProvider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.claude import ClaudeProvider
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function to get LLM provider based on configuration
    """
    provider_name = settings.default_llm_provider.lower()
    
    logger.info(f"Initializing LLM provider: {provider_name}")
    
    if provider_name == 'gemini_2.5' or provider_name.startswith('gemini'):
        return GeminiProvider()
    elif provider_name == 'claude_3.5_sonnet' or provider_name.startswith('claude'):
        return ClaudeProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}. Must be 'gemini_2.5' or 'claude_3.5_sonnet'")
```

### 4. LLM Processing Service

**File:** `app/services/llm_extraction.py`

```python
from app.services.llm.factory import get_llm_provider
from app.db.session import SessionLocal
from app.models.database import Job, InvoiceData
from app.utils.s3 import S3Service
import logging

logger = logging.getLogger(__name__)

class LLMExtractionService:
    def __init__(self):
        self.llm_provider = get_llm_provider()
        self.s3_service = S3Service()
    
    async def extract_from_job(self, job_id: str) -> Dict[str, Any]:
        """
        Extract invoice data using LLM
        
        1. Get OCR text from database
        2. Download PDF pages as images (for vision)
        3. Call LLM provider
        4. Parse and store result
        """
        db = SessionLocal()
        try:
            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Get OCR text from database
            # In a real implementation, you'd combine all OCR text
            # For now, use a placeholder
            ocr_text = "OCR text would be combined from database"
            
            # Download PDF pages as images for vision (optional)
            page_images = {}
            # page_images = await self._download_pages_as_images(job.s3_key)
            
            logger.info(f"Starting LLM extraction with {job.llm_provider}")
            
            # Extract with LLM
            extracted_data = await self.llm_provider.extract_invoice_data(
                ocr_text=ocr_text,
                page_images=page_images
            )
            
            # Store in database
            invoice_data = InvoiceData(
                job_id=job_id,
                invoice_number=extracted_data.get('invoice_number'),
                invoice_date=extracted_data.get('invoice_date'),
                vendor_name=extracted_data.get('vendor_name'),
                total_amount=extracted_data.get('total_amount'),
                currency=extracted_data.get('currency', 'USD'),
                extraction_confidence=extracted_data.get('extraction_confidence', 0.5),
                source_file=job.s3_key,
                extracted_data=extracted_data
            )
            
            db.add(invoice_data)
            db.commit()
            
            logger.info(f"Stored invoice data for job {job_id}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            raise
        finally:
            db.close()
    
    async def _download_pages_as_images(self, s3_key: str) -> Dict[int, Any]:
        """
        Download PDF pages as images (for LLM vision)
        """
        # This would convert PDF to images
        # Implementation would use pdf2image
        pass
```

### 5. Update Celery Task

**File:** `app/workers/tasks.py`

```python
# Update process_pdf_task to include LLM extraction

@celery_app.task(bind=True)
def process_pdf_task(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = "processing"
        job.progress = 10
        db.commit()
        
        # Import services
        from app.services.ocr.factory import get_ocr_provider
        from app.services.llm_extraction import LLMExtractionService
        
        # Initialize services
        ocr_provider = get_ocr_provider()
        llm_service = LLMExtractionService()
        
        # Phase 2: OCR Processing (10-40%)
        logger.info(f"Starting OCR processing for job {job_id}")
        # OCR processing would happen here
        # ocr_result = await ocr_provider.extract_text_from_pdf(...)
        job.progress = 40
        db.commit()
        
        # Phase 3: LLM Extraction (40-90%)
        logger.info(f"Starting LLM extraction for job {job_id}")
        extracted_data = await llm_service.extract_from_job(job_id)
        job.progress = 90
        db.commit()
        
        # Phase 4: Coordinate Mapping (90-100%) - Will be in Phase 4
        # coordinate_mapping_result = await ...
        
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

## Testing

### Test Gemini

```bash
uv run python -c "
from app.services.llm.gemini import GeminiProvider
import asyncio

async def test_gemini():
    provider = GeminiProvider()
    result = await provider.extract_invoice_data(
        ocr_text='Invoice: INV-12345\\nDate: 2025-01-20\\nTotal: $1,234.56',
        page_images={}
    )
    print('Gemini result:', result)

asyncio.run(test_gemini())
"
```

### Test Claude

```bash
uv run python -c "
from app.services.llm.claude import ClaudeProvider
import asyncio

async def test_claude():
    provider = ClaudeProvider()
    result = await provider.extract_invoice_data(
        ocr_text='Invoice: INV-12345\\nDate: 2025-01-20\\nTotal: $1,234.56',
        page_images={}
    )
    print('Claude result:', result)

asyncio.run(test_claude())
"
```

## API Changes

### Update Upload Endpoint

**File:** `app/api/routes/upload.py`

```python
# Add LLM provider validation
valid_llm_providers = ["gemini_2.5", "claude_3.5_sonnet"]
if llm_provider not in valid_llm_providers:
    raise HTTPException(
        status_code=400,
        detail=f"Invalid LLM provider. Must be one of: {valid_llm_providers}"
    )
```

## Success Criteria

- [ ] Gemini 2.5 successfully extracts structured invoice data
- [ ] Claude 3.5 Sonnet successfully extracts structured invoice data
- [ ] LLM provider switching works via .env
- [ ] Response JSON is correctly parsed and validated
- [ ] Confidence scores are calculated
- [ ] Error handling and retry logic in place
- [ ] API calls are properly formatted with prompts
- [ ] Unit tests for LLM services
- [ ] Integration tests with real invoice data

## Next Phase

**Phase 4: Coordinate Mapping & Human Review**
- Map OCR coordinates to extracted fields
- Implement OpenCV highlighting
- Generate annotated images for review
- Create review API endpoints

## Notes

- Both providers support vision capabilities for PDF pages
- Prompts are designed to return JSON directly
- Fallback methods handle cases where structured JSON fails
- Retry logic should be added for production robustness
- API keys must be set in .env before running
