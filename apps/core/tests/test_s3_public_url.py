from apps.core.s3_public_url import storages_custom_domain_from_public_url


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
