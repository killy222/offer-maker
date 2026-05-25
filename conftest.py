"""Pytest fixtures shared across apps."""

import pytest
from django.conf import settings


@pytest.fixture
def english_client(client):
    """Cookie language English (Django set_language / LocaleMiddleware)."""
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
    return client
