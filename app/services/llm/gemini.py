from app.services.llm.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def extract_invoice_data(self, ocr_text: str, page_images: dict) -> dict:
        pass
