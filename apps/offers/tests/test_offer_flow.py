import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.company.models import CompanyProfile


@pytest.mark.django_db
def test_dashboard_shows_company_profile_when_present(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)
    CompanyProfile.objects.create(
        company_name="Main Co",
        vat_number="BG123456789",
        registration_number="REG-001",
        address_line_1="Main street 1",
        city="Sofia",
        postal_code="1000",
        country="Bulgaria",
        phone="+359888123123",
        email="office@mainco.bg",
    )

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert b"Main Co" in response.content


@pytest.mark.django_db
def test_offer_create_redirects_to_company_profile_when_missing(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)

    response = client.get(reverse("offer_create"))

    assert response.status_code == 302
    assert response.url == reverse("company_profile")
