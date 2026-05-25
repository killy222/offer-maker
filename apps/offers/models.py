from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models


class Offer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    client = models.ForeignKey(
        "clients.ClientCompany",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="offers",
    )
    site_address = models.TextField(blank=True)
    offer_date = models.DateField(null=True, blank=True)
    validity_label = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "domain_offers_offer"

    def __str__(self):
        return f"Offer {self.pk}"

    def totals(self) -> dict[str, Decimal]:
        sub = Decimal("0")
        vat_amt = Decimal("0")
        gross = Decimal("0")
        for line in self.lines.all():
            sub += line.line_net()
            vat_amt += line.line_vat_amount()
            gross += line.line_gross()
        q = Decimal("0.01")
        return {
            "subtotal_ex_vat": sub.quantize(q, rounding=ROUND_HALF_UP),
            "vat_amount": vat_amt.quantize(q, rounding=ROUND_HALF_UP),
            "total": gross.quantize(q, rounding=ROUND_HALF_UP),
        }

    def totals_display(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.totals().items()}


class OfferLine(models.Model):
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    catalog_item = models.ForeignKey(
        "products.CatalogItem",
        on_delete=models.PROTECT,
        related_name="offer_lines",
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate_percent = models.DecimalField(max_digits=5, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        db_table = "domain_offers_offerline"

    def line_net(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def line_vat_amount(self) -> Decimal:
        net = self.line_net()
        return (net * self.vat_rate_percent / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def line_gross(self) -> Decimal:
        return (self.line_net() + self.line_vat_amount()).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def __str__(self):
        return f"{self.offer_id}: {self.catalog_item_id}"
