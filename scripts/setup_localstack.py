import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

endpoint_url = "http://localhost:4566"
config = Config(region_name="us-east-1")


def wait_for_localstack(max_retries=30, delay=2):
    print("Waiting for LocalStack to be ready...")
    for i in range(max_retries):
        try:
            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id="test",
                aws_secret_access_key="test",
                config=config,
            )
            client.list_buckets()
            print("✅ LocalStack is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                print(f"❌ Failed to connect to LocalStack: {e}")
                return False


def setup_s3():
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=config,
    )

    bucket_name = "freight-invoices"

    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✅ Created S3 bucket: {bucket_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyExists":
            print(f"✅ S3 bucket already exists: {bucket_name}")
        else:
            raise

    folders = ["uploads/", "processed/", "review-images/"]
    for folder in folders:
        s3.put_object(Bucket=bucket_name, Key=folder)

    print(f"✅ Created folder structure in S3")

    buckets = s3.list_buckets()
    print(f"✅ Available buckets: {[b['Name'] for b in buckets['Buckets']]}")


def setup_textract():
    textract = boto3.client(
        "textract",
        endpoint_url=endpoint_url,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=config,
    )

    print("✅ Amazon Textract client created")
    print("Note: Textract functionality depends on LocalStack version/plan")


def main():
    if not wait_for_localstack():
        return

    print("\n=== Setting up LocalStack Services ===\n")
    setup_s3()
    setup_textract()
    print("\n✅ LocalStack setup complete!\n")


if __name__ == "__main__":
    main()
