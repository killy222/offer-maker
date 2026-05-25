from django.db import migrations


def forwards(apps, schema_editor):
    Offer = apps.get_model("domain_offers", "Offer")
    mapping = {
        "": "",
        "7 days": "7 дни",
        "14 days": "14 дни",
        "30 days": "30 дни",
        "60 days": "60 дни",
    }
    for offer in Offer.objects.all().only("pk", "validity_label"):
        new_val = mapping.get(offer.validity_label, offer.validity_label)
        if new_val != offer.validity_label:
            offer.validity_label = new_val
            offer.save(update_fields=["validity_label"])


def backwards(apps, schema_editor):
    Offer = apps.get_model("domain_offers", "Offer")
    rev = {
        "7 дни": "7 days",
        "14 дни": "14 days",
        "30 дни": "30 days",
        "60 дни": "60 days",
    }
    for offer in Offer.objects.all().only("pk", "validity_label"):
        new_val = rev.get(offer.validity_label, offer.validity_label)
        if new_val != offer.validity_label:
            offer.validity_label = new_val
            offer.save(update_fields=["validity_label"])


class Migration(migrations.Migration):
    dependencies = [
        ("domain_offers", "0003_remove_offer_status"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
