import json
import os

import boto3
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure S3-compatible bucket exists (MinIO)."

    def handle(self, *args, **options):
        if os.getenv("USE_S3_STORAGE", "0") not in {"1", "true", "yes", "on"}:
            self.stdout.write(
                self.style.WARNING("USE_S3_STORAGE is disabled; skipping bucket check.")
            )
            return

        bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "offer-creator-media")
        endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL", "http://minio:9000")
        region_name = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        existing_buckets = [bucket["Name"] for bucket in client.list_buckets().get("Buckets", [])]
        if bucket_name not in existing_buckets:
            client.create_bucket(Bucket=bucket_name)
            self.stdout.write(self.style.SUCCESS(f"Created bucket: {bucket_name}"))

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                }
            ],
        }
        client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        self.stdout.write(self.style.SUCCESS(f"Bucket is ready: {bucket_name}"))
