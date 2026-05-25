from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("company", "0002_create_company_profile_table_if_missing"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyprofile",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="company/logos/"),
        ),
    ]
