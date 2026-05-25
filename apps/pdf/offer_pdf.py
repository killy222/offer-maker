"""Build offer PDF bytes using ReportLab (no native HTML renderer dependency)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.company.models import CompanyProfile
from apps.offers.models import Offer

# Bundled Noto Sans (SIL OFL 1.1, notofonts/noto-fonts) — built-in Helvetica has no Cyrillic.
_PDF_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_PDF_FONT_REGULAR = _PDF_FONT_DIR / "NotoSans-Regular.ttf"
_PDF_FONT_BOLD = _PDF_FONT_DIR / "NotoSans-Bold.ttf"
_PDF_FONT_FAMILY = "OfferPDFSans"
_COLOR_OB_CREAM = colors.HexColor("#FAF7F2")
_COLOR_OB_PEACH_50 = colors.HexColor("#FDF6F3")
_COLOR_OB_PEACH_100 = colors.HexColor("#F8E6DD")
_COLOR_OB_PEACH_600 = colors.HexColor("#B84A28")
_COLOR_OB_PEACH_800 = colors.HexColor("#7A3419")
_COLOR_OB_INK = colors.HexColor("#1C1917")
_COLOR_OB_MUTED = colors.HexColor("#57534E")
_COLOR_OB_LINE = colors.HexColor("#E7E5E4")


def _register_pdf_unicode_fonts() -> str:
    """Register Noto Sans for Paragraph/table text; return family name for fontName."""
    cached = getattr(_register_pdf_unicode_fonts, "_resolved", None)
    if cached is not None:
        return cached
    reg = str(_PDF_FONT_REGULAR.resolve()) if _PDF_FONT_REGULAR.is_file() else None
    bld = str(_PDF_FONT_BOLD.resolve()) if _PDF_FONT_BOLD.is_file() else None
    if not reg or not bld:
        _register_pdf_unicode_fonts._resolved = "Helvetica"
        return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont("OfferPDFSans", reg))
        pdfmetrics.registerFont(TTFont("OfferPDFSansBd", bld))
        pdfmetrics.registerFontFamily(
            _PDF_FONT_FAMILY,
            normal="OfferPDFSans",
            bold="OfferPDFSansBd",
            italic="OfferPDFSans",
            boldItalic="OfferPDFSansBd",
        )
    except Exception:
        _register_pdf_unicode_fonts._resolved = "Helvetica"
        return "Helvetica"
    _register_pdf_unicode_fonts._resolved = _PDF_FONT_FAMILY
    return _PDF_FONT_FAMILY


def _fmt_decimal(d: Decimal) -> str:
    return str(d.quantize(Decimal("0.01")))


def _address_lines(company: CompanyProfile) -> list[str]:
    lines = [
        company.address_line_1,
        company.address_line_2 or "",
        f"{company.postal_code} {company.city}".strip(),
        company.country,
    ]
    return [ln for ln in lines if ln.strip()]


def _company_identity_lines(company: CompanyProfile) -> list[str]:
    lines: list[str] = [company.company_name, *_address_lines(company)]
    if company.vat_number:
        lines.append(f"ДДС: {company.vat_number}")
    if company.registration_number:
        lines.append(f"ЕИК: {company.registration_number}")
    if company.phone:
        lines.append(company.phone)
    if company.email:
        lines.append(company.email)
    return [ln for ln in lines if ln.strip()]


def _offer_header_meta_lines(offer: Offer) -> tuple[list[str], list[str]]:
    issue_date = offer.offer_date or offer.created_at.date()
    valid_until = issue_date + timedelta(days=14)
    if offer.validity_label:
        try:
            valid_until = type(issue_date).fromisoformat(offer.validity_label)
        except ValueError:
            pass

    recipient_lines: list[str] = []
    if offer.client:
        recipient_lines.append(offer.client.name)
        if offer.client.address:
            recipient_lines.append(f"Адрес: {offer.client.address}")
        if offer.client.phone:
            recipient_lines.append(f"Телефон: {offer.client.phone}")
    if offer.site_address:
        recipient_lines.append(f"Обект: {offer.site_address}")
    if not recipient_lines:
        recipient_lines.append("Получател: -")

    meta_lines = [
        f"Дата на издаване: {issue_date.isoformat()}",
        f"Валидно до: {valid_until.isoformat()}",
    ]
    return recipient_lines, meta_lines


def build_offer_pdf(offer: Offer, company: CompanyProfile) -> bytes:
    """Render offer + company branding to PDF bytes."""
    offer = Offer.objects.prefetch_related(
        "lines__catalog_item__unit",
    ).get(pk=offer.pk)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=force_str(_("Offer %(id)s") % {"id": offer.pk}),
    )
    styles = getSampleStyleSheet()
    fn = _register_pdf_unicode_fonts()
    fn_bold = "OfferPDFSansBd" if fn == _PDF_FONT_FAMILY else "Helvetica-Bold"
    h_company = ParagraphStyle(
        "HCompany",
        parent=styles["Heading1"],
        fontName=fn_bold,
        fontSize=17,
        leading=21,
        alignment=1,
        spaceAfter=3,
        textColor=colors.black,
    )
    h_offer_sub = ParagraphStyle(
        "HOfferSub",
        parent=styles["Normal"],
        alignment=1,
        fontName=fn_bold,
        fontSize=10,
        leading=12,
        textColor=colors.black,
        spaceAfter=1,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=fn,
        fontSize=9,
        leading=13,
        textColor=colors.black,
    )
    company_title = ParagraphStyle(
        "CompanyTitle",
        parent=styles["Heading1"],
        fontName=fn_bold,
        fontSize=11,
        leading=13,
        textColor=colors.black,
        spaceAfter=1,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body,
        fontName=fn_bold,
    )
    cell = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName=fn,
        fontSize=8,
        leading=10,
    )
    header_cell = ParagraphStyle(
        "HeaderCell",
        parent=cell,
        fontName=fn_bold,
        fontSize=8,
        leading=10,
        textColor=colors.black,
    )

    story: list = []

    logo_flowable = Spacer(1, 0.1 * cm)
    if company.logo:
        try:
            with company.logo.open("rb") as f:
                raw = f.read()
            # platypus.Image calls os.path.splitext on the first arg; ImageReader is not
            # path-like and raises TypeError — pass a fresh BytesIO instead (ReportLab accepts it).
            logo_flowable = Image(
                BytesIO(raw),
                width=3.2 * cm,
                height=2.4 * cm,
                kind="proportional",
            )
        except OSError:
            logo_flowable = Spacer(1, 0.1 * cm)

    title_block = Table(
        [
            [
                Paragraph("Ценова оферта", h_company),
                logo_flowable,
            ],
            [Paragraph("", h_offer_sub), Spacer(1, 0.01 * cm)],
        ],
        colWidths=[12.5 * cm, 3.5 * cm],
    )
    title_block.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (0, 1)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 1), "CENTER"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(title_block)
    story.append(Spacer(1, 0.5 * cm))

    sender_raw_lines = _company_identity_lines(company)
    sender_raw_lines[0] = f"Фирма: {company.company_name}"
    sender_raw_lines.append("Банкова сметка: -")
    sender_lines = [
        Paragraph(escape(line), body if idx else company_title)
        for idx, line in enumerate(sender_raw_lines)
    ]
    sender_block = Table([[line] for line in sender_lines], colWidths=[10 * cm])
    sender_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ]
        )
    )

    recipient_lines, meta_lines = _offer_header_meta_lines(offer)
    meta_paragraphs = [
        Paragraph(escape(line), body_bold if idx == len(meta_lines) - 1 else body)
        for idx, line in enumerate(meta_lines)
    ] or [Paragraph("", body)]
    meta_block = Table([[line] for line in meta_paragraphs], colWidths=[6 * cm])
    meta_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ]
        )
    )

    recipient_title = Paragraph("Получател", body_bold)
    recipient_lines_only = [Paragraph(escape(line), body) for line in recipient_lines]
    recipient_block = Table(
        [[recipient_title], *[[line] for line in recipient_lines_only]], colWidths=[8 * cm]
    )
    recipient_block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ]
        )
    )
    sender_title = Paragraph("Издател", body_bold)
    sender_block = Table([[sender_title], *sender_block._cellvalues], colWidths=[8 * cm])
    parties_top = Table([[sender_block, recipient_block]], colWidths=[8 * cm, 8 * cm])
    parties_top.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
            ]
        )
    )
    story.append(parties_top)
    story.append(Spacer(1, 0.2 * cm))

    dates_tbl = Table(
        [[Paragraph(escape(meta_lines[0]), body), Paragraph(escape(meta_lines[1]), body_bold)]],
        colWidths=[8 * cm, 8 * cm],
    )
    dates_tbl.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
            ]
        )
    )
    story.append(dates_tbl)
    story.append(Spacer(1, 0.15 * cm))

    hdr_labels = [
        "Описание",
        "Кол.",
        "Мярка",
        "Ед. цена",
        "ДДС %",
        "Нетно",
        "ДДС",
        "Общо",
    ]
    rows: list[list] = [[Paragraph(escape(force_str(h)), header_cell) for h in hdr_labels]]

    for line in offer.lines.all():
        unit_lbl = line.catalog_item.unit.label_bg
        rows.append(
            [
                Paragraph(escape(line.catalog_item.name), cell),
                Paragraph(_fmt_decimal(line.quantity), cell),
                Paragraph(escape(unit_lbl), cell),
                Paragraph(_fmt_decimal(line.unit_price), cell),
                Paragraph(_fmt_decimal(line.vat_rate_percent), cell),
                Paragraph(_fmt_decimal(line.line_net()), cell),
                Paragraph(_fmt_decimal(line.line_vat_amount()), cell),
                Paragraph(_fmt_decimal(line.line_gross()), cell),
            ]
        )

    col_widths = [4.9 * cm, 1.3 * cm, 1.5 * cm, 1.9 * cm, 1.3 * cm, 1.8 * cm, 1.6 * cm, 1.7 * cm]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.black),
                ("GRID", (0, 1), (-1, -1), 0.8, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(tbl)

    totals = offer.totals()
    story.append(Spacer(1, 0.5 * cm))
    tot_rows = [
        ["Сума без ДДС", _fmt_decimal(totals["subtotal_ex_vat"])],
        ["ДДС", _fmt_decimal(totals["vat_amount"])],
        ["Сума за плащане", _fmt_decimal(totals["total"])],
    ]
    tot_tbl = Table(tot_rows, colWidths=[12 * cm, 4 * cm])
    tot_tbl.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), fn),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 2), (-1, 2), fn_bold),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.black),
                ("LINEBELOW", (0, 2), (-1, 2), 0.8, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(tot_tbl)

    doc.build(story)
    out = buf.getvalue()
    return out
