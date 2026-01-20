import boto3
from botocore.config import Config
from app.config import settings
from typing import Optional
import uuid

class S3Service:
    def __init__(self):
        config = Config(region_name=settings.aws_region)
        self.client = boto3.client(
            's3',
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config
        )
        self.bucket = settings.s3_bucket_name
    
    def upload_pdf(self, file_content: bytes, filename: str) -> str:
        key = f"uploads/{uuid.uuid4()}_{filename}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_content,
            ContentType='application/pdf'
        )
        return key
    
    def get_pdf(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
    
    def save_review_image(self, image_data: bytes, job_id: str, page_num: int) -> str:
        key = f"review-images/{job_id}_page_{page_num}.png"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image_data,
            ContentType='image/png'
        )
        return key
    
    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )
    
    def delete_file(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

def get_s3_service() -> S3Service:
    return S3Service()
