from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CatalogItem, Unit

BG_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sht",
        "ъ": "a",
        "ь": "y",
        "ю": "yu",
        "я": "ya",
    }
)


class CatalogItemForm(forms.ModelForm):
    class Meta:
        model = CatalogItem
        fields = ["name", "description", "unit", "base_price", "vat_rate_percent"]
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "unit": _("Unit"),
            "base_price": _("Base price"),
            "vat_rate_percent": _("VAT rate (%)"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit"].queryset = Unit.objects.order_by("sort_order", "pk")
        self.fields["description"].required = False

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError(_("This field is required."))
        return name

    def clean_base_price(self):
        value = self.cleaned_data.get("base_price")
        if value is None:
            raise forms.ValidationError(_("This field is required."))
        if value < 0:
            raise forms.ValidationError(_("Base price cannot be negative."))
        return value

    def clean_vat_rate_percent(self):
        value = self.cleaned_data.get("vat_rate_percent")
        if value is None:
            raise forms.ValidationError(_("This field is required."))
        if value < Decimal("0") or value > Decimal("100"):
            raise forms.ValidationError(_("VAT rate must be between 0 and 100."))
        return value


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ["label_bg", "sort_order"]
        labels = {
            "label_bg": _("Label (Bulgarian)"),
            "sort_order": _("Sort order"),
        }

    def clean_label_bg(self):
        value = (self.cleaned_data.get("label_bg") or "").strip()
        if not value:
            raise forms.ValidationError(_("This field is required."))
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.code = self._build_unique_code(instance.label_bg, instance.pk)
        if commit:
            instance.save()
        return instance

    def _build_unique_code(self, label_bg, instance_pk=None):
        transliterated = label_bg.lower().translate(BG_TO_LATIN)
        pieces = []
        current = []
        for char in transliterated:
            if char.isalnum():
                current.append(char)
            elif current:
                pieces.append("".join(current))
                current = []
        if current:
            pieces.append("".join(current))
        base = "_".join(pieces).upper() or "UNIT"
        candidate = base
        suffix = 2
        qs = Unit.objects.all()
        if instance_pk:
            qs = qs.exclude(pk=instance_pk)
        while qs.filter(code=candidate).exists():
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate
