from io import BytesIO

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import translation
from django.views import View

from apps.company.models import CompanyProfile
from apps.offers.access import get_offer_for_user

from .offer_pdf import build_offer_pdf


class OfferPdfView(LoginRequiredMixin, View):
    """Authenticated PDF download (own offers, or any offer for staff)."""

    def get(self, request, offer_id: int, *args, **kwargs):
        if CompanyProfile.get_solo() is None:
            return HttpResponseRedirect(reverse("company_profile"))
        offer = get_offer_for_user(request.user, offer_id)
        company = CompanyProfile.get_solo()
        with translation.override(request.LANGUAGE_CODE):
            pdf_bytes = build_offer_pdf(offer, company)
        buf = BytesIO(pdf_bytes)
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f"offer-{offer.pk}.pdf",
            content_type="application/pdf",
        )
