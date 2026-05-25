import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clients", "0001_initial_client_company"),
        ("products", "0002_seed_units"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Offer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_address", models.TextField(blank=True)),
                ("offer_date", models.DateField(blank=True, null=True)),
                ("validity_label", models.CharField(blank=True, max_length=64)),
                ("responsible_person", models.CharField(blank=True, max_length=255)),
                (
                    "offer_vat_rate_percent",
                    models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=5),
                ),
                ("status", models.CharField(default="draft", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "client",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="offers",
                        to="clients.clientcompany",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offers",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "domain_offers_offer",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="OfferLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=4, default=Decimal("1"), max_digits=12)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12)),
                ("vat_rate_percent", models.DecimalField(decimal_places=2, max_digits=5)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "catalog_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="offer_lines",
                        to="products.catalogitem",
                    ),
                ),
                (
                    "offer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="domain_offers.offer",
                    ),
                ),
            ],
            options={
                "db_table": "domain_offers_offerline",
                "ordering": ["sort_order", "pk"],
            },
        ),
    ]
