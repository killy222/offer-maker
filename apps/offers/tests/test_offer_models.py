from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db.models import ProtectedError

from apps.offers.models import Offer, OfferLine
from apps.products.models import CatalogItem, Unit


@pytest.mark.django_db
def test_offer_line_net_vat_gross():
    user = User.objects.create_user(username="u1", password="x")
    offer = Offer.objects.create(user=user)
    unit = Unit.objects.get(code="PIECE")
    cat = CatalogItem.objects.create(
        name="Item",
        unit=unit,
        base_price=Decimal("100.00"),
        vat_rate_percent=Decimal("20"),
    )
    line = OfferLine.objects.create(
        offer=offer,
        catalog_item=cat,
        quantity=Decimal("2"),
        unit_price=Decimal("100.00"),
        vat_rate_percent=Decimal("20"),
    )
    assert line.line_net() == Decimal("200.00")
    assert line.line_vat_amount() == Decimal("40.00")
    assert line.line_gross() == Decimal("240.00")


@pytest.mark.django_db
def test_offer_totals_aggregate():
    user = User.objects.create_user(username="u2", password="x")
    offer = Offer.objects.create(user=user)
    unit = Unit.objects.get(code="PIECE")
    cat = CatalogItem.objects.create(
        name="A",
        unit=unit,
        base_price=Decimal("10.00"),
        vat_rate_percent=Decimal("0"),
    )
    OfferLine.objects.create(
        offer=offer,
        catalog_item=cat,
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("0"),
    )
    OfferLine.objects.create(
        offer=offer,
        catalog_item=cat,
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    t = offer.totals()
    assert t["subtotal_ex_vat"] == Decimal("20.00")
    assert t["vat_amount"] == Decimal("2.00")
    assert t["total"] == Decimal("22.00")


@pytest.mark.django_db
def test_catalog_item_protect_when_line_exists():
    user = User.objects.create_user(username="u3", password="x")
    offer = Offer.objects.create(user=user)
    unit = Unit.objects.get(code="PIECE")
    cat = CatalogItem.objects.create(
        name="Del",
        unit=unit,
        base_price=Decimal("1.00"),
        vat_rate_percent=Decimal("0"),
    )
    OfferLine.objects.create(
        offer=offer,
        catalog_item=cat,
        quantity=Decimal("1"),
        unit_price=Decimal("1.00"),
        vat_rate_percent=Decimal("0"),
    )
    with pytest.raises(ProtectedError):
        cat.delete()
