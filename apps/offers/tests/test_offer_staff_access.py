from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.clients.models import ClientCompany
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


@pytest.fixture
def owner_offer(db, catalog_item):
    owner = User.objects.create_user(username="owner", password="x")
    offer = Offer.objects.create(
        user=owner,
        client=ClientCompany.objects.create(name="Acme"),
    )
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )
    return owner, offer


@pytest.mark.django_db
def test_staff_sees_other_users_offer_on_list(client, company_profile, owner_offer):
    _, offer = owner_offer
    admin = User.objects.create_user(username="admin", password="x", is_staff=True)
    client.force_login(admin)

    response = client.get(reverse("offer_list"))

    assert response.status_code == 200
    body = response.content.decode()
    assert str(offer.pk) in body
    assert "Acme" in body


@pytest.mark.django_db
def test_staff_can_open_other_users_offer_detail(client, company_profile, owner_offer):
    _, offer = owner_offer
    admin = User.objects.create_user(username="admin", password="x", is_staff=True)
    client.force_login(admin)

    response = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))

    assert response.status_code == 200


@pytest.mark.django_db
def test_non_staff_still_cannot_open_other_users_offer(client, company_profile, owner_offer):
    _, offer = owner_offer
    other = User.objects.create_user(username="other", password="x", is_staff=False)
    client.force_login(other)

    response = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_staff_can_patch_other_users_offer(client, company_profile, owner_offer):
    _, offer = owner_offer
    admin = User.objects.create_user(username="admin", password="x", is_staff=True)
    client.force_login(admin)

    response = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data='{"site_address": "Admin edit"}',
        content_type="application/json",
    )

    assert response.status_code == 200
    offer.refresh_from_db()
    assert offer.site_address == "Admin edit"


@pytest.mark.django_db
def test_staff_can_download_other_users_offer_pdf(client, company_profile, owner_offer):
    _, offer = owner_offer
    admin = User.objects.create_user(username="admin2", password="x", is_staff=True)
    client.force_login(admin)

    response = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
