"""Build django-storages S3 options for browser-reachable object URLs."""

from __future__ import annotations

from urllib.parse import urlparse


def normalize_public_url(public_url: str) -> str:
    """
    Accept full URLs or bare hostnames (common in Railway env vars).

    ``urlparse("minio.example.app")`` has empty netloc; prepend a scheme first.
    """
    public_url = (public_url or "").strip()
    if not public_url:
        return ""
    parsed = urlparse(public_url)
    if parsed.netloc:
        return public_url
    if public_url.startswith("//"):
        return f"https:{public_url}"
    host = public_url.split("/", 1)[0]
    scheme = "http" if host.startswith("localhost") or host.startswith("127.0.0.1") else "https"
    return f"{scheme}://{public_url.lstrip('/')}"


def storages_custom_domain_from_public_url(
    public_url: str, bucket_name: str
) -> tuple[str | None, str | None]:
    """
    MinIO (path-style) object URLs are ``{origin}/{bucket}/{key}``. django-storages
    with ``custom_domain`` builds ``{protocol}//{custom_domain}/{key}``, so
    ``custom_domain`` must be ``host:port/bucket`` when the browser cannot use the
    Docker-internal endpoint hostname (e.g. ``minio:9000``).
    """
    public_url = normalize_public_url(public_url)
    if not public_url:
        return None, None
    parsed = urlparse(public_url)
    if not parsed.netloc:
        return None, None
    custom_domain = f"{parsed.netloc}/{bucket_name}"
    scheme = parsed.scheme if parsed.scheme in ("http", "https") else "http"
    return custom_domain, f"{scheme}:"
