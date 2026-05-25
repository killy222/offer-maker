"""Build django-storages S3 options for browser-reachable object URLs."""

from __future__ import annotations

from urllib.parse import urlparse


def storages_custom_domain_from_public_url(
    public_url: str, bucket_name: str
) -> tuple[str | None, str | None]:
    """
    MinIO (path-style) object URLs are ``{origin}/{bucket}/{key}``. django-storages
    with ``custom_domain`` builds ``{protocol}//{custom_domain}/{key}``, so
    ``custom_domain`` must be ``host:port/bucket`` when the browser cannot use the
    Docker-internal endpoint hostname (e.g. ``minio:9000``).
    """
    public_url = (public_url or "").strip()
    if not public_url:
        return None, None
    parsed = urlparse(public_url)
    if not parsed.netloc:
        return None, None
    custom_domain = f"{parsed.netloc}/{bucket_name}"
    scheme = parsed.scheme if parsed.scheme in ("http", "https") else "http"
    return custom_domain, f"{scheme}:"
