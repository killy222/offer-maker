import json
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.clients.models import ClientCompany
from apps.company.models import CompanyProfile
from apps.offers.models import Offer
from apps.products.models import CatalogItem, Unit


@pytest.fixture
def operator_user(db):
    return User.objects.create_user(username="op", email="op@x.com", password="pass12345")


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
def test_catalog_search_requires_three_chars(client, operator_user):
    client.force_login(operator_user)
    r = client.get(reverse("catalog_search"), {"q": "ab"})
    assert r.status_code == 200
    assert r.json()["results"] == []


@pytest.mark.django_db
def test_catalog_search_returns_results(client, operator_user, catalog_item):
    client.force_login(operator_user)
    r = client.get(reverse("catalog_search"), {"q": "Til"})
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) >= 1
    assert data["results"][0]["id"] == catalog_item.pk


@pytest.mark.django_db
def test_catalog_search_requires_login(client):
    r = client.get(reverse("catalog_search"), {"q": "abc"})
    assert r.status_code == 302


@pytest.mark.django_db
def test_add_line_defaults_and_totals(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    url_page = f"{reverse('offer_create')}?offer={offer.pk}"
    client.get(url_page)
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("offer_line_add"),
        data=json.dumps({"offer_id": offer.pk, "catalog_item_id": catalog_item.pk}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["lines"]) == 1
    line = data["lines"][0]
    assert line["unit_price"] == "50.00"
    assert line["vat_rate_percent"] == "20.00"
    assert data["totals"]["total"] == "60.00"
    assert "offer_vat_rate_percent" not in data


@pytest.mark.django_db
def test_patch_offer_header(client, operator_user, company_profile):
    client.force_login(operator_user)
    cl = ClientCompany.objects.create(name="ACME")
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_id": cl.pk, "site_address": "Addr 1"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.client_id == cl.pk
    assert offer.site_address == "Addr 1"


@pytest.mark.django_db
def test_offer_create_get_does_not_create_offer_without_query(
    client, operator_user, company_profile
):
    client.force_login(operator_user)
    r = client.get(reverse("offer_create"), follow=False)
    assert r.status_code == 200
    assert Offer.objects.filter(user=operator_user).count() == 0


@pytest.mark.django_db
def test_offer_start_post_creates_offer(client, operator_user, company_profile):
    client.force_login(operator_user)
    client.get(reverse("offer_create"))
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("offer_start"),
        data="{}",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["id"]
    assert Offer.objects.filter(user=operator_user).count() == 1


@pytest.mark.django_db
def test_client_search_requires_three_chars(client, operator_user):
    client.force_login(operator_user)
    r = client.get(reverse("client_search"), {"q": "ab"})
    assert r.status_code == 200
    assert r.json()["results"] == []


@pytest.mark.django_db
def test_client_search_finds_client(client, operator_user):
    client.force_login(operator_user)
    ClientCompany.objects.create(name="Acme Corp")
    r = client.get(reverse("client_search"), {"q": "Acm"})
    assert r.status_code == 200
    assert len(r.json()["results"]) == 1
    assert r.json()["results"][0]["name"] == "Acme Corp"


@pytest.mark.django_db
def test_patch_offer_links_existing_client_by_name_case_insensitive(
    client, operator_user, company_profile
):
    client.force_login(operator_user)
    existing = ClientCompany.objects.create(name="Acme Corp")
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    before = ClientCompany.objects.count()
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_name": "acme corp"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    assert ClientCompany.objects.count() == before
    offer.refresh_from_db()
    assert offer.client_id == existing.pk


@pytest.mark.django_db
def test_patch_offer_creates_client_by_name(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_name": "New Buyer Ltd", "site_address": "1 Main St"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.client is not None
    assert offer.client.name == "New Buyer Ltd"
    assert offer.site_address == "1 Main St"


@pytest.mark.django_db
def test_second_line_uses_catalog_vat_not_offer_field(
    client, operator_user, company_profile, catalog_item
):
    unit = catalog_item.unit
    item2 = CatalogItem.objects.create(
        name="Other",
        unit=unit,
        base_price=Decimal("10.00"),
        vat_rate_percent=Decimal("10"),
    )
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    for cid in (catalog_item.pk, item2.pk):
        r = client.post(
            reverse("offer_line_add"),
            data=json.dumps({"offer_id": offer.pk, "catalog_item_id": cid}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        assert r.status_code == 200
    lines = r.json()["lines"]
    assert lines[0]["vat_rate_percent"] == "20.00"
    assert lines[1]["vat_rate_percent"] == "10.00"


@pytest.mark.django_db
def test_patch_offer_invalid_date_json_error(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"offer_date": "not-a-date"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "date" in r.json().get("error", "").lower()


@pytest.mark.django_db
def test_client_create_api(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("client_create_api"),
        data=json.dumps({"name": "  API Client  "}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "API Client"
    assert ClientCompany.objects.filter(name="API Client").exists()
