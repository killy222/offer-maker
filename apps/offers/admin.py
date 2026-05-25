from django.contrib import admin

from .models import Offer, OfferLine


class OfferLineInline(admin.TabularInline):
    model = OfferLine
    extra = 0
    raw_id_fields = ("catalog_item",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "client", "updated_at")
    inlines = [OfferLineInline]
    raw_id_fields = ("user", "client")


@admin.register(OfferLine)
class OfferLineAdmin(admin.ModelAdmin):
    list_display = ("id", "offer", "catalog_item", "quantity", "unit_price", "vat_rate_percent")
    raw_id_fields = ("offer", "catalog_item")
