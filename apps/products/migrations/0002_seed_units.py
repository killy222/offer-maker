from django.db import migrations


def seed_units(apps, schema_editor):
    Unit = apps.get_model("products", "Unit")
    rows = [
        {"code": "PIECE", "label_bg": "брой", "sort_order": 0},
        {"code": "SQ_M", "label_bg": "м²", "sort_order": 1},
        {"code": "LINEAR_M", "label_bg": "м", "sort_order": 2},
    ]
    for row in rows:
        Unit.objects.update_or_create(code=row["code"], defaults=row)


def unseed_units(apps, schema_editor):
    Unit = apps.get_model("products", "Unit")
    Unit.objects.filter(code__in=["PIECE", "SQ_M", "LINEAR_M"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_units, unseed_units),
    ]
