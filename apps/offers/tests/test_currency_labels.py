from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import translation

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
def test_offer_detail_shows_euro_label_in_bulgarian(client, company_profile, catalog_item):
    user = User.objects.create_user(username="u1", password="pass12345")
    client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )

    with translation.override("bg"):
        response = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))

    assert response.status_code == 200
    body = response.content.decode()
    assert "евро" in body
    assert "лв." not in body


@pytest.mark.django_db
def test_offer_detail_shows_eur_label_in_english(english_client, company_profile, catalog_item):
    user = User.objects.create_user(username="u2", password="pass12345")
    english_client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )

    response = english_client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))

    assert response.status_code == 200
    body = response.content.decode()
    assert "EUR" in body
    assert "лв." not in body
