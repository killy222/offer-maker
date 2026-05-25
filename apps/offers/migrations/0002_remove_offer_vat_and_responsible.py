from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("domain_offers", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="offer",
            name="offer_vat_rate_percent",
        ),
        migrations.RemoveField(
            model_name="offer",
            name="responsible_person",
        ),
    ]
