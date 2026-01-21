import uuid
from typing import Optional

from aiobotocore.session import AioSession
from botocore.config import Config

from src.core.logger import logger
from src.core.settings import settings


class S3Service:
    def __init__(self):
        config = Config(region_name=settings.aws_region)
        self.session = AioSession()
        self.bucket = settings.s3_bucket_name

    async def upload_pdf(self, file_content: bytes, filename: str) -> str:
        key = f"uploads/{uuid.uuid4()}_{filename}"
        async with self.session.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        ) as client:
            await client.put_object(
                Bucket=self.bucket, Key=key, Body=file_content, ContentType="application/pdf"
            )
        logger.info(f"Uploaded PDF to S3: {key}")
        return key

    async def get_pdf(self, key: str) -> bytes:
        async with self.session.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        ) as client:
            response = await client.get_object(Bucket=self.bucket, Key=key)
            return await response["Body"].read()

    async def save_review_image(self, image_data: bytes, job_id: str, page_num: int) -> str:
        key = f"review-images/{job_id}_page_{page_num}.png"
        async with self.session.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        ) as client:
            await client.put_object(
                Bucket=self.bucket, Key=key, Body=image_data, ContentType="image/png"
            )
        logger.info(f"Saved review image to S3: {key}")
        return key

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        import boto3

        sync_client = boto3.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        return sync_client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in
        )

    async def delete_file(self, key: str) -> bool:
        try:
            async with self.session.client(
                "s3",
                endpoint_url=settings.aws_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            ) as client:
                await client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file from S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False


def get_s3_service() -> S3Service:
    return S3Service()
