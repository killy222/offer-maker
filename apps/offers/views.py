import json
from decimal import Decimal
from functools import wraps
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Max, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.dateparse import parse_date
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.clients.models import ClientCompany
from apps.company.models import CompanyProfile
from apps.products.models import CatalogItem

from .access import get_offer_for_user, offer_queryset_for_user, offers_list_queryset_for_user
from .models import Offer, OfferLine
from .validity import VALIDITY_7, VALIDITY_14, VALIDITY_30, VALIDITY_60


def _decimal_or_none(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _line_json(line: OfferLine) -> dict:
    return {
        "id": line.pk,
        "catalog_item_id": line.catalog_item_id,
        "name": line.catalog_item.name,
        "unit_label": line.catalog_item.unit.label_bg,
        "quantity": str(line.quantity),
        "unit_price": str(line.unit_price),
        "vat_rate_percent": str(line.vat_rate_percent),
        "line_net": str(line.line_net()),
        "line_vat_amount": str(line.line_vat_amount()),
        "line_gross": str(line.line_gross()),
    }


def _offer_payload(offer: Offer) -> dict[str, Any]:
    totals = offer.totals()
    return {
        "id": offer.pk,
        "client_id": offer.client_id,
        "client_name": offer.client.name if offer.client else "",
        "site_address": offer.site_address,
        "offer_date": offer.offer_date.isoformat() if offer.offer_date else None,
        "validity_label": offer.validity_label,
        "totals": {k: str(v) for k, v in totals.items()},
        "lines": [
            _line_json(line)
            for line in offer.lines.select_related("catalog_item", "catalog_item__unit").all()
        ],
    }


def _compose_offer_payload() -> dict[str, Any]:
    """Client-side state before an offer row exists (no GET side-effect on /offers/new/)."""
    return {
        "id": None,
        "client_id": None,
        "client_name": "",
        "site_address": "",
        "offer_date": None,
        "validity_label": "",
        "totals": {
            "subtotal_ex_vat": "0.00",
            "vat_amount": "0.00",
            "total": "0.00",
        },
        "lines": [],
    }


def require_json(view_func):
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        if request.method in ("POST", "PATCH"):
            ct = request.content_type or ""
            if "application/json" not in ct:
                return JsonResponse({"error": "Expected application/json"}, status=415)
        return view_func(self, request, *args, **kwargs)

    return _wrapped


class DashboardView(LoginRequiredMixin, ListView):
    """Home and `/offers/` list: paginated offers for the signed-in user."""

    model = Offer
    context_object_name = "offers"
    template_name = "offers/dashboard.html"
    paginate_by = 10

    def get_queryset(self):
        return offers_list_queryset_for_user(self.request.user).select_related("client")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_profile"] = CompanyProfile.get_solo()
        return context


class OfferDetailView(LoginRequiredMixin, DetailView):
    model = Offer
    context_object_name = "offer"
    template_name = "offers/offer_detail.html"

    def get_queryset(self):
        return (
            offer_queryset_for_user(self.request.user)
            .select_related("client", "user")
            .prefetch_related("lines__catalog_item__unit")
        )


class OfferCreateView(LoginRequiredMixin, TemplateView):
    template_name = "offers/offer_create.html"

    def dispatch(self, request, *args, **kwargs):
        if CompanyProfile.get_solo() is None:
            return HttpResponseRedirect(reverse("company_profile"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        offer_id = request.GET.get("offer")
        if offer_id:
            get_offer_for_user(request.user, offer_id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_profile"] = CompanyProfile.get_solo()
        offer_id = self.request.GET.get("offer")
        if offer_id:
            offer = get_offer_for_user(self.request.user, offer_id)
            context["offer"] = offer
            context["offer_payload_dict"] = _offer_payload(offer)
        else:
            context["offer"] = None
            context["offer_payload_dict"] = _compose_offer_payload()
        context["catalog_items"] = CatalogItem.objects.select_related("unit").order_by("name")[:200]
        context["recent_offers"] = offers_list_queryset_for_user(self.request.user)[:12]
        context["today"] = timezone.localdate()
        try:
            context["offer_start_url"] = reverse("offer_start")
        except Exception:
            context["offer_start_url"] = "/offers/api/offers/start/"
        context["validity_options"] = [
            ("", force_str(_("—"))),
            (VALIDITY_7, force_str(_("7 days"))),
            (VALIDITY_14, force_str(_("14 days"))),
            (VALIDITY_30, force_str(_("30 days"))),
            (VALIDITY_60, force_str(_("60 days"))),
        ]
        context["offer_i18n"] = {
            "saved": force_str(_("Saved.")),
            "couldNotStartOffer": force_str(_("Could not start offer.")),
            "saveFailed": force_str(_("Save failed.")),
            "requestFailed": force_str(_("Request failed.")),
            "noLinesYet": force_str(_("No lines yet. Add a product from the catalog.")),
            "validationError": force_str(_("Validation error.")),
            "removeLineTitle": force_str(_("Remove line")),
            "currency": force_str(_("EUR")),
            "catalogSearchPlaceholder": force_str(_("Search (min. 3 characters)…")),
            "clientPlaceholder": force_str(_("Type to search or enter a new name…")),
            "locale": translation.get_language() or "bg",
        }
        return context


class OfferStartView(LoginRequiredMixin, View):
    """Create a persisted offer when the user saves header fields or adds the first line."""

    def post(self, request, *args, **kwargs):
        offer = Offer.objects.create(user=request.user)
        return JsonResponse(_offer_payload(offer))


class CatalogSearchView(LoginRequiredMixin, View):
    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        if len(q) < 3:
            return JsonResponse({"results": []})
        items = (
            CatalogItem.objects.filter(Q(name__icontains=q) | Q(description__icontains=q))
            .select_related("unit")
            .order_by("name")[:25]
        )
        results = [
            {
                "id": item.pk,
                "name": item.name,
                "unit_label": item.unit.label_bg,
                "default_unit_price": str(item.base_price),
                "default_vat_rate_percent": str(item.vat_rate_percent),
            }
            for item in items
        ]
        return JsonResponse({"results": results})


class ClientSearchView(LoginRequiredMixin, View):
    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        if len(q) < 3:
            return JsonResponse({"results": []})
        clients = ClientCompany.objects.filter(name__icontains=q).order_by("name")[:25]
        results = [{"id": c.pk, "name": c.name} for c in clients]
        return JsonResponse({"results": results})


class ClientCreateView(LoginRequiredMixin, View):
    @require_json
    def post(self, request):
        try:
            data = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        name = (data.get("name") or "").strip()
        if not name:
            return JsonResponse({"error": "Name is required."}, status=400)
        client = ClientCompany(name=name)
        try:
            client.full_clean()
            client.save()
        except ValidationError as exc:
            return JsonResponse({"error": exc.message_dict}, status=400)
        return JsonResponse({"id": client.pk, "name": client.name})


class OfferPatchView(LoginRequiredMixin, View):
    @require_json
    def patch(self, request, pk):
        offer = get_offer_for_user(request.user, pk)
        try:
            data = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if "client_id" in data and data.get("client_id") not in (None, "", 0, "0"):
            try:
                offer.client = ClientCompany.objects.get(pk=data["client_id"])
            except (ClientCompany.DoesNotExist, ValueError, TypeError):
                return JsonResponse({"error": "Client not found."}, status=404)
        elif "client_name" in data:
            raw = (data.get("client_name") or "").strip()
            if raw:
                existing = ClientCompany.objects.filter(name__iexact=raw).first()
                if existing:
                    offer.client = existing
                else:
                    client = ClientCompany(name=raw)
                    try:
                        client.full_clean()
                        client.save()
                    except ValidationError as exc:
                        return JsonResponse({"error": exc.message_dict}, status=400)
                    offer.client = client
            else:
                offer.client = None
        elif "client_id" in data:
            offer.client = None
        if "site_address" in data:
            offer.site_address = data["site_address"] or ""
        if "offer_date" in data:
            od = data["offer_date"]
            if not od:
                offer.offer_date = None
            else:
                parsed = parse_date(str(od))
                if parsed is None:
                    return JsonResponse({"error": "Invalid offer date."}, status=400)
                offer.offer_date = parsed
        if "validity_label" in data:
            offer.validity_label = data["validity_label"] or ""
        offer.save()
        return JsonResponse(_offer_payload(offer))


class OfferLineAddView(LoginRequiredMixin, View):
    @require_json
    def post(self, request):
        try:
            data = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        offer = get_offer_for_user(request.user, data.get("offer_id"))
        catalog_item = get_object_or_404(CatalogItem, pk=data.get("catalog_item_id"))
        max_sort = offer.lines.aggregate(m=Max("sort_order"))["m"]
        next_sort = (max_sort if max_sort is not None else -1) + 1
        line = OfferLine.objects.create(
            offer=offer,
            catalog_item=catalog_item,
            quantity=Decimal("1"),
            unit_price=catalog_item.base_price,
            vat_rate_percent=catalog_item.vat_rate_percent,
            sort_order=next_sort,
        )
        payload = _offer_payload(offer)
        payload["added_line"] = _line_json(line)
        return JsonResponse(payload)


class OfferLinePatchView(LoginRequiredMixin, View):
    @require_json
    def patch(self, request, pk):
        line = get_object_or_404(OfferLine.objects.select_related("offer"), pk=pk)
        get_offer_for_user(request.user, line.offer_id)
        try:
            data = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        if "quantity" in data:
            q = _decimal_or_none(data["quantity"])
            if q is None or q <= 0:
                return JsonResponse({"error": "Invalid quantity"}, status=400)
            line.quantity = q
        if "unit_price" in data:
            p = _decimal_or_none(data["unit_price"])
            if p is None or p < 0:
                return JsonResponse({"error": "Invalid unit price"}, status=400)
            line.unit_price = p
        if "vat_rate_percent" in data:
            v = _decimal_or_none(data["vat_rate_percent"])
            if v is None or v < 0 or v > 100:
                return JsonResponse({"error": "Invalid VAT"}, status=400)
            line.vat_rate_percent = v
        line.save()
        offer = line.offer
        return JsonResponse(_offer_payload(offer))

    def delete(self, request, pk):
        line = get_object_or_404(OfferLine, pk=pk)
        get_offer_for_user(request.user, line.offer_id)
        offer = line.offer
        line.delete()
        return JsonResponse(_offer_payload(offer))
