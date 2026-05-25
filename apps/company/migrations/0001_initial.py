from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="CompanyProfile",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("company_name", models.CharField(max_length=255)),
                        ("vat_number", models.CharField(max_length=64, unique=True)),
                        ("registration_number", models.CharField(max_length=64, unique=True)),
                        ("address_line_1", models.CharField(max_length=255)),
                        ("address_line_2", models.CharField(blank=True, max_length=255)),
                        ("city", models.CharField(max_length=128)),
                        ("postal_code", models.CharField(max_length=32)),
                        ("country", models.CharField(max_length=128)),
                        ("phone", models.CharField(max_length=64)),
                        ("email", models.EmailField(max_length=254)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"ordering": ["-updated_at"], "db_table": "offers_companyprofile"},
                )
            ],
            database_operations=[],
        )
    ]
