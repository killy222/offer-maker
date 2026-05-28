from apps.core.s3_public_url import (
    normalize_public_url,
    storages_custom_domain_from_public_url,
)


def test_empty_public_url_returns_none():
    assert storages_custom_domain_from_public_url("", "b") == (None, None)
    assert storages_custom_domain_from_public_url("   ", "b") == (None, None)


def test_localhost_minio_path_style():
    cd, proto = storages_custom_domain_from_public_url(
        "http://localhost:9000", "offer-creator-media"
    )
    assert cd == "localhost:9000/offer-creator-media"
    assert proto == "http:"


def test_https_public_origin():
    cd, proto = storages_custom_domain_from_public_url("https://cdn.example.com", "my-bucket")
    assert cd == "cdn.example.com/my-bucket"
    assert proto == "https:"


def test_invalid_scheme_defaults_to_http():
    cd, proto = storages_custom_domain_from_public_url("ftp://files.example:9000", "b")
    assert cd == "files.example:9000/b"
    assert proto == "http:"


def test_bare_hostname_gets_https_scheme():
    assert (
        normalize_public_url("minio-production-a8ef.up.railway.app")
        == "https://minio-production-a8ef.up.railway.app"
    )


def test_bare_railway_hostname_builds_custom_domain():
    cd, proto = storages_custom_domain_from_public_url(
        "minio-production-a8ef.up.railway.app",
        "offer-creator-media",
    )
    assert cd == "minio-production-a8ef.up.railway.app/offer-creator-media"
    assert proto == "https:"
