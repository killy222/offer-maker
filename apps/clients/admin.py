from django.contrib import admin

from .models import ClientCompany


@admin.register(ClientCompany)
class ClientCompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "updated_at")
    search_fields = ("name", "address", "phone")
