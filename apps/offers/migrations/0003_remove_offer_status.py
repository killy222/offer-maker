from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("domain_offers", "0002_remove_offer_vat_and_responsible"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="offer",
            name="status",
        ),
    ]
