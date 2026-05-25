import io
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from pypdf import PdfReader

from apps.company.models import CompanyProfile
from apps.offers.models import Offer, OfferLine
from apps.products.models import CatalogItem, Unit


@pytest.fixture
def company_profile(db):
    return CompanyProfile.objects.create(
        company_name="Main Co",
        vat_number="BG1",
        registration_number="R1",
        address_line_1="St 1",
        city="Sofia",
        postal_code="1000",
        country="BG",
        phone="+359",
        email="a@b.c",
    )


@pytest.fixture
def catalog_item(db):
    unit = Unit.objects.get(code="PIECE")
    return CatalogItem.objects.create(
        name="Tile",
        unit=unit,
        base_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )


@pytest.mark.django_db
def test_dashboard_default_language_bulgarian(client, company_profile):
    user = User.objects.create_user(username="i18nbg", password="pass12345")
    client.force_login(user)
    r = client.get(reverse("dashboard"))
    assert r.status_code == 200
    text = r.content.decode()
    assert "Оферти" in text


@pytest.mark.django_db
def test_set_language_to_english(client, company_profile):
    user = User.objects.create_user(username="i18nen", password="pass12345")
    client.force_login(user)
    r0 = client.get(reverse("dashboard"))
    assert "Оферти" in r0.content.decode()
    r1 = client.post(
        reverse("set_language"),
        {"language": "en", "next": reverse("dashboard")},
    )
    assert r1.status_code == 302
    r2 = client.get(reverse("dashboard"))
    assert r2.status_code == 200
    assert "Offers" in r2.content.decode()


@pytest.mark.django_db
def test_offer_pdf_text_bulgarian_default(client, company_profile, catalog_item):
    user = User.objects.create_user(username="pdfbg", password="pass12345")
    client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    r = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))
    assert r.status_code == 200
    body = b"".join(r.streaming_content)
    reader = PdfReader(io.BytesIO(body))
    text = "".join((page.extract_text() or "") for page in reader.pages)
    assert "оферта" in text.lower()


@pytest.mark.django_db
def test_offer_pdf_text_always_bulgarian_regardless_of_session(
    english_client, company_profile, catalog_item
):
    """PDF is always in Bulgarian even when session language is English."""
    user = User.objects.create_user(username="pdfen", password="pass12345")
    english_client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    r = english_client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))
    assert r.status_code == 200
    body = b"".join(r.streaming_content)
    reader = PdfReader(io.BytesIO(body))
    text = "".join((page.extract_text() or "") for page in reader.pages)
    assert "оферта" in text.lower()
    assert "Сума за плащане" in text
