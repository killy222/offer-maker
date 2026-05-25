from django.urls import path

from apps.pdf.views import OfferPdfView

from .views import (
    CatalogSearchView,
    ClientCreateView,
    ClientSearchView,
    DashboardView,
    OfferCreateView,
    OfferDetailView,
    OfferLineAddView,
    OfferLinePatchView,
    OfferPatchView,
    OfferStartView,
)

_dashboard_view = DashboardView.as_view()

urlpatterns = [
    path("", _dashboard_view, name="dashboard"),
    path("offers/", _dashboard_view, name="offer_list"),
    path("offers/new/", OfferCreateView.as_view(), name="offer_create"),
    path("offers/<int:offer_id>/pdf/", OfferPdfView.as_view(), name="offer_pdf"),
    path("offers/<int:pk>/", OfferDetailView.as_view(), name="offer_detail"),
    path("offers/api/catalog-search/", CatalogSearchView.as_view(), name="catalog_search"),
    path("offers/api/client-search/", ClientSearchView.as_view(), name="client_search"),
    path("offers/api/clients/", ClientCreateView.as_view(), name="client_create_api"),
    path("offers/api/offers/start/", OfferStartView.as_view(), name="offer_start"),
    path("offers/api/offers/<int:pk>/", OfferPatchView.as_view(), name="offer_patch"),
    path("offers/api/lines/add/", OfferLineAddView.as_view(), name="offer_line_add"),
    path(
        "offers/api/lines/<int:pk>/",
        OfferLinePatchView.as_view(),
        name="offer_line_patch",
    ),
]
