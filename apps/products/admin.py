from django.contrib import admin

from .models import CatalogItem, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("code", "label_bg", "sort_order")
    ordering = ("sort_order", "pk")


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "base_price", "vat_rate_percent", "updated_at")
    list_select_related = ("unit",)
    search_fields = ("name", "description")
