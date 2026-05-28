import json
import os

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError

from apps.core.s3_client import s3_client_from_env


class Command(BaseCommand):
    help = "Ensure S3-compatible bucket exists (MinIO)."

    def handle(self, *args, **options):
        if os.getenv("USE_S3_STORAGE", "0") not in {"1", "true", "yes", "on"}:
            self.stdout.write(
                self.style.WARNING("USE_S3_STORAGE is disabled; skipping bucket check.")
            )
            return

        client, cfg = s3_client_from_env()
        bucket_name = cfg["bucket_name"]
        endpoint_url = cfg["endpoint_url"]

        self.stdout.write(f"S3 endpoint: {endpoint_url}")
        self.stdout.write(f"S3 bucket: {bucket_name}")

        try:
            client.head_bucket(Bucket=bucket_name)
            self.stdout.write(self.style.SUCCESS(f"Bucket exists: {bucket_name}"))
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise CommandError(
                    f"Cannot access bucket {bucket_name!r} at {endpoint_url}: {exc}"
                ) from exc

            self.stdout.write(f"Creating bucket: {bucket_name}")
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
        try:
            client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        except ClientError as exc:
            raise CommandError(f"Could not set bucket policy on {bucket_name}: {exc}") from exc

        probe_key = "media/.bucket-probe"
        client.put_object(Bucket=bucket_name, Key=probe_key, Body=b"ok")
        client.delete_object(Bucket=bucket_name, Key=probe_key)

        self.stdout.write(self.style.SUCCESS(f"Bucket is ready: {bucket_name}"))
