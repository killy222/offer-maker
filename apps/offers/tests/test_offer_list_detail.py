from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

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


@pytest.mark.django_db
def test_offer_list_requires_login(client):
    r = client.get(reverse("offer_list"))
    assert r.status_code == 302
    assert r.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_offer_list_shows_non_empty_offers(english_client, company_profile, catalog_item):
    user = User.objects.create_user(username="u1", password="pass12345")
    english_client.force_login(user)
    empty = Offer.objects.create(user=user)
    with_client = Offer.objects.create(user=user, client=ClientCompany.objects.create(name="Acme"))
    with_line = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=with_line,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )

    r = english_client.get(reverse("offer_list"))
    assert r.status_code == 200
    body = r.content.decode()
    assert f"Offer #{with_client.pk}" in body
    assert f"Offer #{with_line.pk}" in body
    assert f"Offer #{empty.pk}" not in body


@pytest.mark.django_db
def test_offer_list_paginates_ten_per_page(english_client, company_profile):
    user = User.objects.create_user(username="pager", password="pass12345")
    english_client.force_login(user)
    client_co = ClientCompany.objects.create(name="Buyer")
    offers = [Offer.objects.create(user=user, client=client_co) for _ in range(11)]
    base = timezone.now()
    for i, o in enumerate(offers):
        Offer.objects.filter(pk=o.pk).update(updated_at=base - timedelta(seconds=i))
    oldest_on_second_page = offers[10]

    r1 = english_client.get(reverse("offer_list"))
    assert r1.status_code == 200
    body1 = r1.content.decode()
    assert body1.count("Offer #") == 10
    assert f"Offer #{oldest_on_second_page.pk}" not in body1

    r2 = english_client.get(reverse("dashboard") + "?page=2")
    assert r2.status_code == 200
    assert f"Offer #{oldest_on_second_page.pk}" in r2.content.decode()


@pytest.mark.django_db
def test_offer_list_other_users_offers_hidden(english_client, company_profile):
    a = User.objects.create_user(username="a", password="x")
    b = User.objects.create_user(username="b", password="x")
    o = Offer.objects.create(user=a, client=ClientCompany.objects.create(name="Only A"))
    english_client.force_login(b)
    r = english_client.get(reverse("offer_list"))
    assert r.status_code == 200
    assert f"Offer #{o.pk}" not in r.content.decode()


@pytest.mark.django_db
def test_offer_detail_owner_ok(client, company_profile, catalog_item):
    user = User.objects.create_user(username="u2", password="pass12345")
    client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=2,
        unit_price=10,
        vat_rate_percent=20,
    )

    r = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))
    assert r.status_code == 200
    assert b"Tile" in r.content


@pytest.mark.django_db
def test_offer_detail_requires_login(client, company_profile, catalog_item):
    user = User.objects.create_user(username="anon", password="x")
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )
    r = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))
    assert r.status_code == 302
    assert r.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_offer_detail_other_user_404(client, company_profile, catalog_item):
    owner = User.objects.create_user(username="o", password="x")
    other = User.objects.create_user(username="p", password="x")
    offer = Offer.objects.create(user=owner)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=1,
        unit_price=10,
        vat_rate_percent=20,
    )
    client.force_login(other)
    r = client.get(reverse("offer_detail", kwargs={"pk": offer.pk}))
    assert r.status_code == 404
