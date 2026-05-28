import os

import boto3
from botocore.config import Config


def s3_settings_from_env():
    """Read S3/MinIO settings from env (same names as config.settings)."""
    return {
        "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME", "offer-creator-media").strip(),
        "endpoint_url": os.getenv("AWS_S3_ENDPOINT_URL", "http://minio:9000").strip(),
        "region_name": os.getenv("AWS_S3_REGION_NAME", "us-east-1").strip(),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID", "minioadmin").strip(),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin").strip(),
        "addressing_style": os.getenv("AWS_S3_ADDRESSING_STYLE", "path").strip() or "path",
    }


def s3_client_from_env():
    """Boto3 S3 client aligned with django-storages (path-style for MinIO)."""
    cfg = s3_settings_from_env()
    client = boto3.client(
        "s3",
        endpoint_url=cfg["endpoint_url"],
        region_name=cfg["region_name"],
        aws_access_key_id=cfg["access_key"],
        aws_secret_access_key=cfg["secret_key"],
        config=Config(s3={"addressing_style": cfg["addressing_style"]}),
    )
    return client, cfg
