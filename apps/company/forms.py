from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CompanyProfile


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "company_name",
            "vat_number",
            "registration_number",
            "address_line_1",
            "address_line_2",
            "city",
            "postal_code",
            "country",
            "phone",
            "email",
            "logo",
        ]
        labels = {
            "company_name": _("Company name"),
            "vat_number": _("VAT number"),
            "registration_number": _("Registration number"),
            "address_line_1": _("Address line 1"),
            "address_line_2": _("Address line 2"),
            "city": _("City"),
            "postal_code": _("Postal code"),
            "country": _("Country"),
            "phone": _("Phone"),
            "email": _("Email"),
            "logo": _("Company logo"),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:
            return logo

        allowed_types = {"image/png", "image/jpeg", "image/webp"}
        content_type = getattr(logo, "content_type", "")
        if content_type and content_type not in allowed_types:
            raise forms.ValidationError(_("Logo must be PNG, JPEG, or WEBP."))

        max_size = 5 * 1024 * 1024
        if logo.size > max_size:
            raise forms.ValidationError(_("Logo must be 5 MB or smaller."))

        return logo
