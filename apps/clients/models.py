from django.core.exceptions import ValidationError
from django.db import models


class ClientCompany(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = "clients_clientcompany"

    def clean(self):
        super().clean()
        if not self.name or not str(self.name).strip():
            raise ValidationError({"name": "This field is required."})

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
