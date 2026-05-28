"""Offer visibility: operators see only their offers; staff (admin) see all."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .models import Offer


def offer_queryset_for_user(user):
    """Offers the user may access (all offers for staff, own offers otherwise)."""
    if user.is_staff:
        return Offer.objects.all()
    return Offer.objects.filter(user=user)


def get_offer_for_user(user, pk):
    return get_object_or_404(offer_queryset_for_user(user), pk=pk)


def offers_list_queryset_for_user(user):
    """Offers visible in list/sidebar: hide abandoned compose rows (no lines and no header data)."""
    return (
        offer_queryset_for_user(user)
        .annotate(line_count=Count("lines"))
        .filter(
            ~(
                Q(line_count=0)
                & Q(client__isnull=True)
                & Q(site_address="")
                & Q(offer_date__isnull=True)
                & Q(validity_label="")
            )
        )
        .order_by("-updated_at")
    )
