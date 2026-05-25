from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("company", "0003_add_logo_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="companyprofile",
            name="vat_number",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name="companyprofile",
            name="registration_number",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
