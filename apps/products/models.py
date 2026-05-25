from decimal import ROUND_HALF_UP, Decimal

from django.db import models


class Unit(models.Model):
    code = models.CharField(max_length=32, unique=True)
    label_bg = models.CharField(max_length=64)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "pk"]
        db_table = "products_unit"

    def __str__(self):
        return self.label_bg


class CatalogItem(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="catalog_items",
    )
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_rate_percent = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = "products_catalogitem"

    @property
    def final_price(self) -> Decimal:
        rate = self.vat_rate_percent / Decimal("100")
        gross = self.base_price * (Decimal("1") + rate)
        return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __str__(self):
        return self.name
