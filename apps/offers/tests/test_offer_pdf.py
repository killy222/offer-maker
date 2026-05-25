import zlib
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from apps.company.models import CompanyProfile
from apps.offers.models import Offer, OfferLine
from apps.pdf.offer_pdf import _company_identity_lines, _offer_header_meta_lines
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
def test_offer_pdf_owner_ok(client, company_profile, catalog_item):
    user = User.objects.create_user(username="op", email="op@x.com", password="pass12345")
    client.force_login(user)
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("2"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )

    r = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))

    assert r.status_code == 200
    assert r["Content-Type"] == "application/pdf"
    assert "attachment" in r["Content-Disposition"]
    body = b"".join(r.streaming_content)
    assert body[:4] == b"%PDF"


@pytest.mark.django_db
def test_offer_pdf_wrong_user_404(client, company_profile, catalog_item):
    owner = User.objects.create_user(username="owner", password="pass12345")
    other = User.objects.create_user(username="other", password="pass12345")
    offer = Offer.objects.create(user=owner)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=catalog_item,
        quantity=Decimal("1"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    client.force_login(other)

    r = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))

    assert r.status_code == 404


@pytest.mark.django_db
def test_offer_pdf_redirects_when_company_profile_missing(client, catalog_item):
    user = User.objects.create_user(username="op", password="pass12345")
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

    assert r.status_code == 302
    assert r.url == reverse("company_profile")


@pytest.mark.django_db
def test_offer_pdf_anonymous_redirects_login(client, company_profile, catalog_item):
    user = User.objects.create_user(username="owner", password="pass12345")
    offer = Offer.objects.create(user=user)

    r = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))

    assert r.status_code == 302
    assert r.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_offer_pdf_includes_cyrillic_line_text(client, company_profile):
    """Noto-backed PDF must embed Cyrillic (Helvetica shows tofu)."""
    user = User.objects.create_user(username="opcyr", email="c@x.com", password="pass12345")
    client.force_login(user)
    unit = Unit.objects.create(code="CYR_PCS", label_bg="бр.", sort_order=999)
    cat = CatalogItem.objects.create(
        name="Плочки",
        unit=unit,
        base_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )
    offer = Offer.objects.create(user=user)
    OfferLine.objects.create(
        offer=offer,
        catalog_item=cat,
        quantity=Decimal("2"),
        unit_price=Decimal("10.00"),
        vat_rate_percent=Decimal("20"),
    )

    r = client.get(reverse("offer_pdf", kwargs={"offer_id": offer.pk}))
    body = b"".join(r.streaming_content)

    assert r.status_code == 200
    assert b"/Subtype /TrueType" in body
    decompressed = bytearray()
    for seg in body.split(b"stream\n")[1:]:
        raw, _, _ = seg.partition(b"endstream")
        chunk = raw.strip(b"\r\n")
        try:
            decompressed.extend(zlib.decompress(chunk))
        except zlib.error:
            pass
    inner = bytes(decompressed)
    # TTF subset uses a CMap with Unicode code points (UTF-8 literals may not appear in streams).
    assert b"NotoSans-Regular" in body or b"NotoSans-Bold" in body
    assert b"041F" in inner and b"043B" in inner  # U+041F П, U+043B л from "Плочки"
    assert b"0431" in inner and b"0440" in inner  # б, р from unit label "бр."


def test_company_identity_lines_are_ordered_and_compact(company_profile):
    lines = _company_identity_lines(company_profile)

    assert lines[0] == "Main Co"
    assert "St 1" in lines
    assert "1000 Sofia" in lines
    assert "BG" in lines
    assert any("BG1" in line for line in lines)
    assert any("R1" in line for line in lines)
    assert "+359" in lines
    assert "a@b.c" in lines
    assert all(line.strip() for line in lines)


@pytest.mark.django_db
def test_offer_header_meta_lines_include_dates_and_recipient():
    user = User.objects.create_user(username="metauser", password="pass12345")
    offer = Offer.objects.create(user=user)
    offer.site_address = "Site 1"
    offer.validity_label = "7 days"

    recipient_lines, meta_lines = _offer_header_meta_lines(offer)

    assert any("Site 1" in line for line in recipient_lines)
    assert any("Issue" in line or "Дата" in line for line in meta_lines)
    assert any("Valid" in line or "Валид" in line for line in meta_lines)


@pytest.mark.django_db
def test_offer_header_meta_lines_fallback_validity_period():
    user = User.objects.create_user(username="metauser2", password="pass12345")
    offer = Offer.objects.create(user=user)

    _, meta_lines = _offer_header_meta_lines(offer)

    assert len(meta_lines) == 2
