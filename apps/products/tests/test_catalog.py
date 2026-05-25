from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.urls import reverse

from apps.offers.models import Offer, OfferLine
from apps.products.models import CatalogItem, Unit


@pytest.mark.django_db
def test_seed_three_units_bulgarian_labels():
    assert Unit.objects.count() == 3
    piece = Unit.objects.get(code="PIECE")
    sq = Unit.objects.get(code="SQ_M")
    m = Unit.objects.get(code="LINEAR_M")
    assert piece.label_bg == "брой"
    assert sq.label_bg == "м²"
    assert m.label_bg == "м"
    assert list(Unit.objects.order_by("sort_order", "pk").values_list("code", flat=True)) == [
        "PIECE",
        "SQ_M",
        "LINEAR_M",
    ]


@pytest.mark.django_db
def test_final_price_zero_vat():
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Widget",
        unit=unit,
        base_price=Decimal("100.00"),
        vat_rate_percent=Decimal("0"),
    )
    assert item.final_price == Decimal("100.00")


@pytest.mark.django_db
def test_final_price_twenty_percent():
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Widget",
        unit=unit,
        base_price=Decimal("100.00"),
        vat_rate_percent=Decimal("20"),
    )
    assert item.final_price == Decimal("120.00")


@pytest.mark.django_db
def test_final_price_rounds_half_up():
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Widget",
        unit=unit,
        base_price=Decimal("0.03"),
        vat_rate_percent=Decimal("20"),
    )
    assert item.final_price == Decimal("0.04")


@pytest.mark.django_db
def test_unit_delete_protects_when_referenced():
    unit = Unit.objects.get(code="PIECE")
    CatalogItem.objects.create(
        name="X",
        unit=unit,
        base_price=Decimal("1.00"),
        vat_rate_percent=Decimal("0"),
    )
    with pytest.raises(ProtectedError):
        unit.delete()


@pytest.mark.django_db
def test_catalog_list_requires_login(client):
    response = client.get(reverse("catalog_list"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_catalog_create_flow(client):
    user = User.objects.create_user(username="op", email="op@example.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.get(code="SQ_M")
    response = client.post(
        reverse("catalog_create"),
        {
            "name": "Flooring",
            "description": "Oak boards",
            "unit": str(unit.pk),
            "base_price": "50.00",
            "vat_rate_percent": "20",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("catalog_list")
    item = CatalogItem.objects.get(name="Flooring")
    assert item.unit_id == unit.pk
    assert item.base_price == Decimal("50.00")
    assert item.final_price == Decimal("60.00")


@pytest.mark.django_db
def test_catalog_create_rejects_negative_base(client):
    user = User.objects.create_user(username="op2", email="op2@example.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.get(code="PIECE")
    response = client.post(
        reverse("catalog_create"),
        {
            "name": "Bad",
            "description": "",
            "unit": str(unit.pk),
            "base_price": "-1",
            "vat_rate_percent": "0",
        },
    )
    assert response.status_code == 200
    assert CatalogItem.objects.filter(name="Bad").count() == 0


@pytest.mark.django_db
def test_catalog_create_rejects_vat_over_100(client):
    user = User.objects.create_user(username="op3", email="op3@example.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.get(code="PIECE")
    response = client.post(
        reverse("catalog_create"),
        {
            "name": "Bad vat",
            "description": "",
            "unit": str(unit.pk),
            "base_price": "10",
            "vat_rate_percent": "100.01",
        },
    )
    assert response.status_code == 200
    assert not CatalogItem.objects.filter(name="Bad vat").exists()


@pytest.mark.django_db
def test_catalog_list_shows_final_price(client):
    user = User.objects.create_user(username="op4", email="op4@example.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.get(code="LINEAR_M")
    CatalogItem.objects.create(
        name="Cable run",
        unit=unit,
        base_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    response = client.get(reverse("catalog_list"))
    assert response.status_code == 200
    assert b"Cable run" in response.content
    # Default locale is Bulgarian (comma decimal separator).
    assert b"12,00" in response.content or b"12.00" in response.content


@pytest.mark.django_db
def test_catalog_edit_updates_values(client):
    user = User.objects.create_user(username="op5", email="op5@example.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Consulting",
        unit=unit,
        base_price=Decimal("100.00"),
        vat_rate_percent=Decimal("20"),
    )
    response = client.post(
        reverse("catalog_edit", kwargs={"pk": item.pk}),
        {
            "name": "Consulting",
            "description": "",
            "unit": str(unit.pk),
            "base_price": "200.00",
            "vat_rate_percent": "0",
        },
    )
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.base_price == Decimal("200.00")
    assert item.final_price == Decimal("200.00")


@pytest.mark.django_db
def test_catalog_delete_requires_login(client):
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Lonely",
        unit=unit,
        base_price=Decimal("1.00"),
        vat_rate_percent=Decimal("0"),
    )
    r = client.post(reverse("catalog_delete", kwargs={"pk": item.pk}))
    assert r.status_code == 302
    assert CatalogItem.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_catalog_delete_post_removes_when_unused(english_client):
    user = User.objects.create_user(username="cdel1", email="cd1@example.com", password="pass12345")
    english_client.force_login(user)
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="Orphan item",
        unit=unit,
        base_price=Decimal("5.00"),
        vat_rate_percent=Decimal("0"),
    )
    r = english_client.post(reverse("catalog_delete", kwargs={"pk": item.pk}), follow=True)
    assert r.status_code == 200
    assert r.redirect_chain[0][0] == reverse("catalog_list")
    assert not CatalogItem.objects.filter(pk=item.pk).exists()
    content = r.content.decode()
    assert "was deleted" in content


@pytest.mark.django_db
def test_catalog_delete_blocked_when_used_on_offer(english_client):
    user = User.objects.create_user(username="cdel2", email="cd2@example.com", password="pass12345")
    english_client.force_login(user)
    unit = Unit.objects.get(code="PIECE")
    item = CatalogItem.objects.create(
        name="In use",
        unit=unit,
        base_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=item,
        quantity=1,
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    r = english_client.post(reverse("catalog_delete", kwargs={"pk": item.pk}), follow=True)
    assert r.status_code == 200
    assert CatalogItem.objects.filter(pk=item.pk).exists()
    assert "Cannot delete" in r.content.decode()


@pytest.mark.django_db
def test_catalog_create_with_each_unit_type(client):
    user = User.objects.create_user(username="op6", email="op6@example.com", password="pass12345")
    client.force_login(user)
    for code in ("PIECE", "SQ_M", "LINEAR_M"):
        unit = Unit.objects.get(code=code)
        name = f"Item-{code}"
        resp = client.post(
            reverse("catalog_create"),
            {
                "name": name,
                "description": "",
                "unit": str(unit.pk),
                "base_price": "1",
                "vat_rate_percent": "0",
            },
        )
        assert resp.status_code == 302, code
    assert CatalogItem.objects.count() == 3


@pytest.mark.django_db
def test_units_list_requires_login(client):
    response = client.get(reverse("unit_list"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_units_create_requires_login(client):
    response = client.get(reverse("unit_create"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_units_edit_requires_login(client):
    unit = Unit.objects.create(code="CUSTOM_UNIT", label_bg="custom", sort_order=99)
    response = client.get(reverse("unit_edit", kwargs={"pk": unit.pk}))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_units_delete_requires_login(client):
    unit = Unit.objects.create(code="DELETE_ME", label_bg="delete", sort_order=99)
    response = client.post(reverse("unit_delete", kwargs={"pk": unit.pk}))
    assert response.status_code == 302
    assert reverse("login") in response.url
    assert Unit.objects.filter(pk=unit.pk).exists()


@pytest.mark.django_db
def test_units_create_auto_generates_code(client):
    user = User.objects.create_user(
        username="unitop1", email="unit1@example.com", password="pass12345"
    )
    client.force_login(user)
    response = client.post(
        reverse("unit_create"),
        {
            "label_bg": "пакет",
            "sort_order": 7,
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("unit_list")
    unit = Unit.objects.get(label_bg="пакет")
    assert unit.code.startswith("PAKET")
    assert unit.sort_order == 7


@pytest.mark.django_db
def test_units_create_handles_code_collisions(client):
    user = User.objects.create_user(
        username="unitop2", email="unit2@example.com", password="pass12345"
    )
    client.force_login(user)
    Unit.objects.create(code="PAKET", label_bg="пакет", sort_order=1)
    response = client.post(
        reverse("unit_create"),
        {
            "label_bg": "пакет",
            "sort_order": 2,
        },
    )
    assert response.status_code == 302
    created = Unit.objects.get(label_bg="пакет", sort_order=2)
    assert created.code == "PAKET_2"


@pytest.mark.django_db
def test_units_edit_regenerates_code_when_label_changes(client):
    user = User.objects.create_user(
        username="unitop3", email="unit3@example.com", password="pass12345"
    )
    client.force_login(user)
    unit = Unit.objects.create(code="OLD_CODE", label_bg="старо", sort_order=1)
    response = client.post(
        reverse("unit_edit", kwargs={"pk": unit.pk}),
        {
            "label_bg": "ново",
            "sort_order": 5,
        },
    )
    assert response.status_code == 302
    unit.refresh_from_db()
    assert unit.code.startswith("NOVO")
    assert unit.label_bg == "ново"
    assert unit.sort_order == 5


@pytest.mark.django_db
def test_units_delete_post_removes_when_unused(english_client):
    user = User.objects.create_user(
        username="unitdel1", email="unitdel1@example.com", password="pass12345"
    )
    english_client.force_login(user)
    unit = Unit.objects.create(code="ORPHAN_U", label_bg="свободна", sort_order=10)
    response = english_client.post(
        reverse("unit_delete", kwargs={"pk": unit.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert response.redirect_chain[0][0] == reverse("unit_list")
    assert not Unit.objects.filter(pk=unit.pk).exists()
    assert "was deleted" in response.content.decode()


@pytest.mark.django_db
def test_units_delete_blocked_when_used(english_client):
    user = User.objects.create_user(
        username="unitdel2", email="unitdel2@example.com", password="pass12345"
    )
    english_client.force_login(user)
    unit = Unit.objects.create(code="USED_U", label_bg="ползвана", sort_order=11)
    CatalogItem.objects.create(
        name="Depends",
        unit=unit,
        base_price=Decimal("1.00"),
        vat_rate_percent=Decimal("20"),
    )
    response = english_client.post(
        reverse("unit_delete", kwargs={"pk": unit.pk}),
        follow=True,
    )
    assert response.status_code == 200
    assert Unit.objects.filter(pk=unit.pk).exists()
    assert "Cannot delete" in response.content.decode()
