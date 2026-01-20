# Phase 5: Export Generation & Data Validation

## Overview

Phase 5 focuses on implementing export functionality (JSON/Excel), data validation rules, and a human correction workflow.

## Objectives

- [ ] Implement JSON export with metadata
- [ ] Implement Excel export with formatting
- [ ] Add data validation rules
- [ ] Implement correction submission validation
- [ ] Create export API endpoints
- [ ] Handle large datasets efficiently

## Implementation Tasks

### 1. Export Service

**File:** `app/services/export.py`

```python
import json
from typing import Dict, List, Any, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
from app.models.database import Job, InvoiceData
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        pass
    
    def export_to_json(
        self, 
        job_id: str,
        db: SessionLocal
    ) -> Dict[str, Any]:
        """
        Export extracted data as JSON with metadata
        
        Returns:
            Dictionary with invoice data, metadata, and timestamps
        """
        try:
            # Get job and invoice data
            job = db.query(Job).filter(Job.id == job_id).first()
            invoice_data = db.query(InvoiceData).filter(
                InvoiceData.job_id == job_id
            ).first()
            
            if not invoice_data:
                raise ValueError(f"No invoice data found for job {job_id}")
            
            # Build export structure
            export_data = {
                "invoice": invoice_data.extracted_data,
                "metadata": {
                    "job_id": job_id,
                    "file_name": job.file_name,
                    "s3_key": job.s3_key,
                    "ocr_provider": job.ocr_provider,
                    "llm_provider": job.llm_provider,
                    "extraction_timestamp": invoice_data.extraction_timestamp.isoformat() if invoice_data.extraction_timestamp else None,
                    "extraction_confidence": invoice_data.extraction_confidence
                },
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_version": "1.0.0"
            }
            
            logger.info(f"Exported job {job_id} to JSON")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting job {job_id} to JSON: {e}")
            raise
    
    def export_to_excel(
        self, 
        job_id: str,
        db: SessionLocal
    ) -> bytes:
        """
        Export extracted data as Excel with formatting
        
        Returns:
            Excel file as bytes
        """
        try:
            # Get invoice data
            invoice_data = db.query(InvoiceData).filter(
                InvoiceData.job_id == job_id
            ).first()
            
            if not invoice_data:
                raise ValueError(f"No invoice data found for job {job_id}")
            
            data = invoice_data.extracted_data
            
            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Freight Invoice"
            
            # Header information
            headers = [
                "Invoice Number",
                "Invoice Date",
                "Vendor Name",
                "Vendor Address",
                "Total Amount",
                "Currency",
                "Bill of Lading",
                "Shipment ID",
                "Origin",
                "Destination",
                "Weight",
                "Weight Unit",
                "Subtotal",
                "Payment Terms",
                "Due Date"
            ]
            
            # Add header row with styling
            for col_num, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D3D3D3D", end_color="D3D3D3D")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Add data
            row_num = 2
            ws.cell(row=row_num, column=1).value = data.get('invoice_number', '')
            ws.cell(row=row_num, column=2).value = data.get('invoice_date', '')
            ws.cell(row=row_num, column=3).value = data.get('vendor_name', '')
            ws.cell(row=row_num, column=4).value = data.get('vendor_address', '')
            ws.cell(row=row_num, column=5).value = data.get('total_amount', '')
            ws.cell(row=row_num, column=6).value = data.get('currency', 'USD')
            ws.cell(row=row_num, column=7).value = data.get('bill_of_lading', '')
            ws.cell(row_num, column=8).value = data.get('shipment_id', '')
            ws.cell(row=row_num, column=9).value = data.get('origin', '')
            ws.cell(row=row_num, column=10).value = data.get('destination', '')
            ws.cell(row=row_num, column=11).value = data.get('weight', '')
            ws.cell(row=row_num, column=12).value = data.get('weight_unit', '')
            ws.cell(row=row_num, column=13).value = data.get('subtotal', '')
            ws.cell(row_num, column=14).value = data.get('payment_terms', '')
            ws.cell(row=row_num, column=15).value = data.get('due_date', '')
            
            # Add line items in separate sheet
            ws_line_items = wb.create_sheet(title="Line Items")
            
            line_item_headers = ["Description", "Quantity", "Unit", "Unit Price", "Total", "Service Type"]
            for col_num, header in enumerate(line_item_headers, start=1):
                cell = ws_line_items.cell(row=1, column=col_num)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D3D3D3D", end_color="D3D3D3D")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            line_items = data.get('line_items', [])
            for item_num, item in enumerate(line_items, start=2):
                ws_line_items.cell(row=item_num, column=1).value = item.get('description', '')
                ws_line_items.cell(row=item_num, column=2).value = item.get('quantity', '')
                ws_line_items.cell(row=item_num, column=3).value = item.get('unit', '')
                ws_line_items.cell(row=item_num, column=4).value = item.get('unit_price', '')
                ws_line_items.cell(row=item_num, column=5).value = item.get('total', '')
                ws_line_items.cell(row=item_num, column=6).value = item.get('service_type', '')
            
            # Add taxes in separate sheet
            ws_taxes = wb.create_sheet(title="Taxes")
            
            tax_headers = ["Tax Type", "Rate", "Amount"]
            for col_num, header in enumerate(tax_headers, start=1):
                cell = ws_taxes.cell(row=1, column=col_num)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D3D3D3D", end_color="D3D3D3D")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            taxes = data.get('taxes', [])
            for tax_num, tax in enumerate(taxes, start=2):
                ws_taxes.cell(row=tax_num, column=1).value = tax.get('tax_type', '')
                ws_taxes.cell(row=tax_num, column=2).value = tax.get('rate', '')
                ws_taxes.cell(row=tax_num, column=3).value = tax.get('amount', '')
            
            # Add surcharges in separate sheet
            ws_surcharges = wb.create_sheet(title="Surcharges")
            
            surcharge_headers = ["Charge Type", "Amount"]
            for col_num, header in enumerate(surcharge_headers, start=1):
                cell = ws_surcharges.cell(row=1, column=col_num)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D3D3D3D", end_color="D3D3D3D")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            surcharges = data.get('surcharges', [])
            for surcharge_num, surcharge in enumerate(surcharges, start=2):
                ws_surcharges.cell(row=surcharge_num, column=1).value = surcharge.get('charge_type', '')
                ws_surcharges.cell(row=surcharge_num, column=2).value = surcharge.get('amount', '')
            
            # Adjust column widths
            for ws in [ws, ws_line_items, ws_taxes, ws_surcharges]:
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        if cell.value:
                            cell_length = len(str(cell.value))
                            if cell_length > max_length:
                                max_length = cell_length
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter] = adjusted_width
            
            # Save to bytes
            from io import BytesIO
            output = BytesIO()
            wb.save(output)
            excel_data = output.getvalue()
            
            logger.info(f"Exported job {job_id} to Excel")
            return excel_data
            
        except Exception as e:
            logger.error(f"Error exporting job {job_id} to Excel: {e}")
            raise
```

### 2. Data Validation Service

**File:** `app/services/validation.py`

```python
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from app.models.schemas import FreightInvoice
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self):
        # Validation rules
        self.required_fields = [
            'invoice_number',
            'invoice_date',
            'vendor_name',
            'total_amount'
        ]
        
        self.numeric_fields = [
            'total_amount',
            'subtotal',
            'taxes',
            'surcharges'
        ]
    
    def validate_invoice_data(
        self, 
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate extracted invoice data
        
        Returns:
            (is_valid: bool, errors: list[str])
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if not data.get(field):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate invoice date
        if 'invoice_date' in data and data['invoice_date']:
            if not self._validate_date(data['invoice_date']):
                errors.append(f"Invalid invoice date: {data['invoice_date']}")
        
        # Validate numeric fields
        for field in self.numeric_fields:
            if field in data:
                value = data[field]
                
                if isinstance(value, list):
                    # List of items (taxes, surcharges, line_items)
                    for item in value:
                        if isinstance(item, dict) and 'amount' in item:
                            if not self._validate_amount(item['amount']):
                                errors.append(f"Invalid amount in {field}: {item['amount']}")
                elif value is not None:
                    if not self._validate_amount(value):
                        errors.append(f"Invalid {field}: {value}")
        
        # Validate totals match
        if 'total_amount' in data and 'subtotal' in data:
            subtotal = data['subtotal'] or 0
            taxes = data.get('taxes', [])
            surcharges = data.get('surcharges', [])
            
            total_tax = sum(tax.get('amount', 0) for tax in taxes)
            total_surcharge = sum(surcharge.get('amount', 0) for surcharge in surcharges)
            
            calculated_total = Decimal(str(subtotal)) + Decimal(str(total_tax)) + Decimal(str(total_surcharge))
            extracted_total = Decimal(str(data['total_amount']))
            
            if abs(calculated_total - extracted_total) > Decimal('0.01'):
                errors.append(f"Total mismatch: calculated {calculated_total} != extracted {extracted_total}")
        
        # Validate line items
        if 'line_items' in data:
            line_items = data['line_items']
            for item_num, item in enumerate(line_items):
                if 'total' in item and 'quantity' in item and 'unit_price' in item:
                    try:
                        calculated = Decimal(str(item.get('quantity', 0))) * Decimal(str(item.get('unit_price', 0)))
                        extracted = Decimal(str(item['total']))
                        
                        if abs(calculated - extracted) > Decimal('0.01'):
                            errors.append(f"Line item {item_num}: total mismatch")
                    except (InvalidOperation, TypeError):
                        errors.append(f"Line item {item_num}: Invalid numeric values")
        
        # Validate confidence score
        if 'extraction_confidence' in data:
            confidence = data['extraction_confidence']
            if not (0 <= confidence <= 1):
                errors.append(f"Invalid confidence score: {confidence}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Invoice data validation passed")
        else:
            logger.warning(f"Validation failed with {len(errors)} errors: {errors}")
        
        return is_valid, errors
    
    def _validate_date(self, date_value: str) -> bool:
        """
        Validate date format (YYYY-MM-DD)
        """
        try:
            parsed_date = datetime.strptime(date_value, "%Y-%m-%d").date()
            # Check if date is reasonable (not in future, not too old)
            today = date.today()
            one_year_ago = today.replace(year=today.year - 1)
            
            if parsed_date > today:
                return False
            if parsed_date < one_year_ago:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_amount(self, amount: Any) -> bool:
        """
        Validate amount is a positive number
        """
        try:
            decimal_amount = Decimal(str(amount))
            return decimal_amount > 0
        except (InvalidOperation, TypeError, ValueError):
            return False
    
    def validate_correction(
        self,
        field_name: str,
        old_value: Any,
        new_value: Any
    ) -> bool:
        """
        Validate a correction submission
        """
        # Check if new value is different
        if str(old_value) == str(new_value):
            logger.warning(f"Correction for '{field_name}' has same value")
            return False
        
        # Validate field type
        if field_name in ['total_amount', 'subtotal', 'taxes', 'surcharges']:
            if not self._validate_amount(new_value):
                logger.error(f"Invalid amount correction for '{field_name}': {new_value}")
                return False
        
        if field_name == 'invoice_date':
            if not self._validate_date(new_value):
                logger.error(f"Invalid date correction for '{field_name}': {new_value}")
                return False
        
        return True
```

### 3. Export API Endpoints

**File:** `app/api/routes/export.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Job
from app.services.export import ExportService
from app.services.validation import ValidationService
from app.models.schemas import FreightInvoice
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["export"])
export_service = ExportService()
validation_service = ValidationService()

@router.get("/jobs/{job_id}/export/json")
async def export_job_json(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Export job data as JSON
    
    Returns:
        JSON file with invoice data and metadata
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Job not ready for export. Current status: {job.status}"
            )
        
        # Export data
        export_data = export_service.export_to_json(job_id, db)
        
        # Return as downloadable JSON
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=export_data,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={job.file_name}_invoice.json"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting job {job_id} to JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/jobs/{job_id}/export/excel")
async def export_job_excel(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Export job data as Excel file
    
    Returns:
        Excel file with formatted invoice data
    """
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Job not ready for export. Current status: {job.status}"
            )
        
        # Export data
        excel_data = export_service.export_to_excel(job_id, db)
        
        # Return as downloadable Excel
        return StreamingResponse(
            content=excel_data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={job.file_name}_invoice.xlsx"
            }
        )
    
    except Exception as e:
        logger.error(f"Error exporting job {job_id} to Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/jobs/{job_id}/validate")
async def validate_job_data(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Validate extracted data for a job
    
    Returns:
        Validation results with errors
    """
    try:
        from app.models.database import InvoiceData
        invoice_data = db.query(InvoiceData).filter(
            InvoiceData.job_id == job_id
        ).first()
        
        if not invoice_data:
            raise HTTPException(status_code=404, detail="Invoice data not found")
        
        # Validate
        is_valid, errors = validation_service.validate_invoice_data(
            invoice_data.extracted_data
        )
        
        return {
            "job_id": job_id,
            "is_valid": is_valid,
            "errors": errors,
            "error_count": len(errors)
        }
    
    except Exception as e:
        logger.error(f"Error validating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
```

### 4. Update Main Application

**File:** `app/main.py`

Add export router:

```python
from app.api.routes import upload, status, data, download, export

app.include_router(export.router)  # Add export router
```

### 5. Update Makefile

**File:** `Makefile`

```makefile
# Add export targets

export-json: ## Export job data as JSON
	@echo "Exporting as JSON requires job_id"
	@echo "Usage: make export-json JOB_ID={job_id}"

export-excel: ## Export job data as Excel
	@echo "Exporting as Excel requires job_id"
	@echo "Usage: make export-excel JOB_ID={job_id}"

validate-job: ## Validate job data
	@echo "Validating job data requires job_id"
	@echo "Usage: make validate-job JOB_ID={job_id}"
```

### 6. Database Migrations

```bash
# Create migration for export tracking
uv run alembic revision --autogenerate -m "add export tracking"
uv run alembic upgrade head
```

## Testing

### Test JSON Export

```bash
# Export job as JSON
curl http://localhost:8000/api/v1/jobs/{job_id}/export/json \
  -o invoice.json

# View structure
cat invoice.json | python -m json.tool
```

### Test Excel Export

```bash
# Export job as Excel
curl http://localhost:8000/api/v1/jobs/{job_id}/export/excel \
  -o invoice.xlsx

# Verify Excel file
file invoice.xlsx
```

### Test Validation

```bash
# Validate job data
curl -X POST http://localhost:8000/api/v1/jobs/{job_id}/validate

# Expected response:
{
  "job_id": "...",
  "is_valid": true/false,
  "errors": [],
  "error_count": 0
}
```

## Success Criteria

- [ ] JSON export returns properly formatted data with metadata
- [ ] Excel export returns downloadable file with formatting
- [ ] Excel contains multiple sheets (Main, Line Items, Taxes, Surcharges)
- [ ] Excel has proper styling (headers, colors, alignment)
- [ ] Validation rules catch missing required fields
- [ ] Validation rules detect numeric format errors
- [ ] Validation rules detect date format errors
- [ ] Validation rules detect total calculation mismatches
- [ ] Validation rules detect line item total mismatches
- [ ] API endpoints return appropriate status codes
- [ ] Error handling is comprehensive with logging
- [ ] Large exports complete within reasonable time
- [ ] Unit tests for export service
- [ ] Unit tests for validation service
- [ ] Integration tests with real invoice data

## Next Phase

**Phase 6: Testing & Deployment**
- Write comprehensive unit tests
- Create integration test suite
- Set up E2E testing
- Configure CI/CD pipeline
- Prepare deployment documentation
- Create monitoring dashboards
- Implement logging and alerting
- Create disaster recovery procedures

## Notes

- Excel uses openpyxl with styling
- JSON export includes metadata and timestamps
- Validation uses Decimal for precise financial calculations
- Confidence scores help identify low-quality extractions
- Export endpoints check job status before allowing export
- Streaming response for large Excel files to avoid memory issues
