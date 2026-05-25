from django.db import models


class CompanyProfile(models.Model):
    company_name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=64, blank=True, null=True)
    registration_number = models.CharField(max_length=64, blank=True, null=True)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=128)
    phone = models.CharField(max_length=64)
    email = models.EmailField()
    logo = models.ImageField(upload_to="company/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        db_table = "offers_companyprofile"

    def save(self, *args, **kwargs):
        if not self.pk and CompanyProfile.objects.exists():
            raise ValueError("Only one CompanyProfile is allowed.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        return cls.objects.first()

    def __str__(self):
        return self.company_name
