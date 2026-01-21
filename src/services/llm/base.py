from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    @abstractmethod
    async def extract_invoice_data(self, ocr_text: str, page_images: dict) -> dict:
        pass
