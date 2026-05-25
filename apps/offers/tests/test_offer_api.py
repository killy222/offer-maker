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


# ---------------------------------------------------------------------------
# Coverage: require_json decorator (line 111)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_require_json_rejects_non_json_content_type(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("client_create_api"),
        data="name=test",
        content_type="application/x-www-form-urlencoded",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 415
    assert "application/json" in r.json()["error"]


# ---------------------------------------------------------------------------
# Coverage: ClientCreateView error paths (lines 248-252, 257-258)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_client_create_api_invalid_json(client, operator_user, company_profile):
    client.force_login(operator_user)
    client.get(reverse("offer_create"))
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("client_create_api"),
        data="{bad json",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "Invalid JSON" in r.json()["error"]


@pytest.mark.django_db
def test_client_create_api_empty_name(client, operator_user, company_profile):
    client.force_login(operator_user)
    client.get(reverse("offer_create"))
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("client_create_api"),
        data=json.dumps({"name": "   "}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "required" in r.json()["error"].lower()


# ---------------------------------------------------------------------------
# Coverage: OfferPatchView error paths (lines 268-269, 274-275, 291, 293)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patch_offer_invalid_json(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data="{bad",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "Invalid JSON" in r.json()["error"]


@pytest.mark.django_db
def test_patch_offer_invalid_client_id(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_id": 99999}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 404
    assert "Client not found" in r.json()["error"]


@pytest.mark.django_db
def test_patch_offer_clear_client_with_empty_name(client, operator_user, company_profile):
    client.force_login(operator_user)
    cl = ClientCompany.objects.create(name="OldClient")
    offer = Offer.objects.create(user=operator_user, client=cl)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_name": ""}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.client is None


@pytest.mark.django_db
def test_patch_offer_clear_client_with_null_client_id(client, operator_user, company_profile):
    client.force_login(operator_user)
    cl = ClientCompany.objects.create(name="SomeClient")
    offer = Offer.objects.create(user=operator_user, client=cl)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"client_id": None}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.client is None


@pytest.mark.django_db
def test_patch_offer_clear_date(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"offer_date": ""}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.offer_date is None


@pytest.mark.django_db
def test_patch_offer_set_validity_label(client, operator_user, company_profile):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_patch", kwargs={"pk": offer.pk}),
        data=json.dumps({"validity_label": "30 days"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    offer.refresh_from_db()
    assert offer.validity_label == "30 days"


# ---------------------------------------------------------------------------
# Coverage: OfferLineAddView invalid JSON (lines 316-317)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_offer_line_add_invalid_json(client, operator_user, company_profile):
    client.force_login(operator_user)
    client.get(reverse("offer_create"))
    token = client.cookies["csrftoken"].value
    r = client.post(
        reverse("offer_line_add"),
        data="{bad json",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "Invalid JSON" in r.json()["error"]


# ---------------------------------------------------------------------------
# Coverage: OfferLinePatchView.patch (lines 338-361)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_patch_line_quantity_and_price(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        data=json.dumps({"quantity": "3", "unit_price": "25.00"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    line.refresh_from_db()
    assert line.quantity == Decimal("3")
    assert line.unit_price == Decimal("25.00")


@pytest.mark.django_db
def test_patch_line_invalid_quantity(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        data=json.dumps({"quantity": "0"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "quantity" in r.json()["error"].lower()


@pytest.mark.django_db
def test_patch_line_invalid_unit_price(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        data=json.dumps({"unit_price": "-5"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "price" in r.json()["error"].lower()


@pytest.mark.django_db
def test_patch_line_invalid_vat(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        data=json.dumps({"vat_rate_percent": "150"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400
    assert "vat" in r.json()["error"].lower()


@pytest.mark.django_db
def test_patch_line_invalid_json(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.patch(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        data="{bad",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Coverage: OfferLinePatchView.delete (lines 364-368)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_line(client, operator_user, company_profile, catalog_item):
    client.force_login(operator_user)
    offer = Offer.objects.create(user=operator_user)
    from apps.offers.models import OfferLine

    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.get(f"{reverse('offer_create')}?offer={offer.pk}")
    token = client.cookies["csrftoken"].value
    r = client.delete(
        reverse("offer_line_patch", kwargs={"pk": line.pk}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert r.status_code == 200
    assert OfferLine.objects.filter(pk=line.pk).count() == 0
    assert r.json()["totals"]["total"] == "0.00"


# ---------------------------------------------------------------------------
# Coverage: _decimal_or_none helper (lines 28-30)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_decimal_or_none_helper():
    from apps.offers.views import _decimal_or_none

    assert _decimal_or_none(None) is None
    assert _decimal_or_none("") is None
    assert _decimal_or_none("3.14") == Decimal("3.14")
    assert _decimal_or_none(42) == Decimal("42")
