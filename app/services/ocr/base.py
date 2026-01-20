from abc import ABC, abstractmethod
from typing import List, Dict
from app.models.schemas import OCRBoundingBox

class BaseOCRProvider(ABC):
    
    @abstractmethod
    async def extract_text_from_pdf(
        self, 
        pdf_path: str
    ) -> Dict[int, List[OCRBoundingBox]]:
        pass
    
    @abstractmethod
    async def extract_text_from_image(
        self, 
        image_bytes: bytes
    ) -> List[OCRBoundingBox]:
        pass
