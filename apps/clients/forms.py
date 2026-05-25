from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ClientCompany


class ClientCompanyForm(forms.ModelForm):
    class Meta:
        model = ClientCompany
        fields = ["name", "address", "phone"]
        labels = {
            "name": _("Client name"),
            "address": _("Address"),
            "phone": _("Phone"),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError(_("This field is required."))
        return name
