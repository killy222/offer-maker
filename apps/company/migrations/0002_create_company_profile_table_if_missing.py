from django.db import migrations


def create_company_profile_table_if_missing(apps, schema_editor):
    model = apps.get_model("company", "CompanyProfile")
    table_names = schema_editor.connection.introspection.table_names()
    if model._meta.db_table not in table_names:
        schema_editor.create_model(model)


class Migration(migrations.Migration):
    dependencies = [
        ("company", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_company_profile_table_if_missing,
            migrations.RunPython.noop,
        )
    ]
