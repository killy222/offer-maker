import io

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.company.models import CompanyProfile


def build_small_png():
    file_obj = io.BytesIO()
    image = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
    image.save(file_obj, format="PNG")
    return file_obj.getvalue()


@pytest.mark.django_db
def test_company_profile_singleton_guard():
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

    with pytest.raises(ValueError):
        CompanyProfile.objects.create(
            company_name="Second Co",
            vat_number="BG987654321",
            registration_number="REG-002",
            address_line_1="Second street 2",
            city="Plovdiv",
            postal_code="4000",
            country="Bulgaria",
            phone="+359888999999",
            email="office@second.bg",
        )


@pytest.mark.django_db
def test_company_profile_page_requires_auth(client):
    response = client.get(reverse("company_profile"))

    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_create_company_profile_flow(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)

    response = client.post(
        reverse("company_profile"),
        {
            "company_name": "Main Co",
            "vat_number": "BG123456789",
            "registration_number": "REG-001",
            "address_line_1": "Main street 1",
            "address_line_2": "",
            "city": "Sofia",
            "postal_code": "1000",
            "country": "Bulgaria",
            "phone": "+359888123123",
            "email": "office@mainco.bg",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("company_profile")
    profile = CompanyProfile.get_solo()
    assert profile.company_name == "Main Co"


@pytest.mark.django_db
def test_create_company_profile_flow_allows_empty_vat_and_registration(client):
    user = User.objects.create_user(
        username="operator2", email="op2@example.com", password="pass12345"
    )
    client.force_login(user)

    response = client.post(
        reverse("company_profile"),
        {
            "company_name": "Main Co",
            "vat_number": "",
            "registration_number": "",
            "address_line_1": "Main street 1",
            "address_line_2": "",
            "city": "Sofia",
            "postal_code": "1000",
            "country": "Bulgaria",
            "phone": "+359888123123",
            "email": "office@mainco.bg",
        },
    )

    assert response.status_code == 302
    profile = CompanyProfile.get_solo()
    assert profile.vat_number in ("", None)
    assert profile.registration_number in ("", None)


@pytest.mark.django_db
def test_create_company_profile_with_logo(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)

    logo = SimpleUploadedFile("logo.png", build_small_png(), content_type="image/png")
    response = client.post(
        reverse("company_profile"),
        {
            "company_name": "Main Co",
            "vat_number": "BG123456789",
            "registration_number": "REG-001",
            "address_line_1": "Main street 1",
            "address_line_2": "",
            "city": "Sofia",
            "postal_code": "1000",
            "country": "Bulgaria",
            "phone": "+359888123123",
            "email": "office@mainco.bg",
            "logo": logo,
        },
    )

    assert response.status_code == 302
    profile = CompanyProfile.get_solo()
    assert profile.logo.name.endswith(".png")


@pytest.mark.django_db
def test_company_profile_page_renders_logo_preview(client):
    user = User.objects.create_user(
        username="operator", email="op@example.com", password="pass12345"
    )
    client.force_login(user)
    logo = SimpleUploadedFile("logo.png", build_small_png(), content_type="image/png")
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
        logo=logo,
    )

    response = client.get(reverse("company_profile"))

    assert response.status_code == 200
    assert "Текущо лого".encode() in response.content
