# MinIO on Railway

## Error: "executable server could not be found"

Railway tried to run `server` as the program. The MinIO binary is `minio`; `server` is only a subcommand.

**Wrong (causes this error):**

```text
server /data --console-address :9001
```

**Correct — pick one:**

1. **Leave Start Command empty** and deploy from this directory (`deploy/minio`) using the Dockerfile here (recommended).
2. **Or** set Start Command to the full command:

   ```text
   minio server /data --console-address :9001
   ```

3. **Or** use Docker image `minio/minio` with **Custom Start Command cleared** and add a volume at `/data`.

## Railway checklist (minio service)

1. **New service** → deploy from repo, **Root Directory**: `deploy/minio`
2. **Volume**: mount `/data`
3. **Variables**: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (strong values)
4. **Networking**: generate public domain on port **9000** (API)
5. **Private networking**: note private host (e.g. `minio.railway.internal`)

## offer-maker variables

| Variable | Example |
|----------|---------|
| `USE_S3_STORAGE` | `1` |
| `AWS_ACCESS_KEY_ID` | same as `MINIO_ROOT_USER` |
| `AWS_SECRET_ACCESS_KEY` | same as `MINIO_ROOT_PASSWORD` |
| `AWS_STORAGE_BUCKET_NAME` | `offer-creator-media` |
| `AWS_S3_ENDPOINT_URL` | `http://minio.railway.internal:9000` (your private host) |
| `AWS_S3_PUBLIC_URL` | `https://your-minio.up.railway.app` (include `https://`; bare hostname also works after deploy) |
| `AWS_S3_REGION_NAME` | `us-east-1` |
| `AWS_S3_ADDRESSING_STYLE` | `path` |

## offer-maker start command

```bash
/bin/sh -c 'python manage.py ensure_s3_bucket && python manage.py migrate && python manage.py collectstatic --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --access-logfile - --error-logfile -'
```

Requires `gunicorn` in `requirements.txt`.

After deploy, **Deploy logs** must show:

```text
S3 endpoint: http://minio.railway.internal:9000
S3 bucket: offer-creator-media
Bucket is ready: offer-creator-media
```

If you see `USE_S3_STORAGE is disabled; skipping`, uploads will still fail when `USE_S3_STORAGE=1` at runtime only if vars differ (they should not).

### Still `NoSuchBucket` on upload?

1. `AWS_S3_ENDPOINT_URL` must be the **private** MinIO host (`http://<minio-service>.railway.internal:9000`), not `http://minio:9000` (Docker-only) unless Railway resolves that name.
2. `AWS_STORAGE_BUCKET_NAME` must match the bucket name exactly (default `offer-creator-media`).
3. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` must match MinIO `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`.
4. Run once via SSH: `python manage.py ensure_s3_bucket` and read the printed endpoint/bucket.
5. In MinIO console → Buckets, confirm the same name exists on **that** MinIO instance.
