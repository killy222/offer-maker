from django.urls import path

from .views import (
    CatalogItemCreateView,
    CatalogItemDeleteView,
    CatalogItemListView,
    CatalogItemUpdateView,
    UnitCreateView,
    UnitDeleteView,
    UnitListView,
    UnitUpdateView,
)

urlpatterns = [
    path("catalog/", CatalogItemListView.as_view(), name="catalog_list"),
    path("catalog/new/", CatalogItemCreateView.as_view(), name="catalog_create"),
    path(
        "catalog/<int:pk>/delete/",
        CatalogItemDeleteView.as_view(),
        name="catalog_delete",
    ),
    path(
        "catalog/<int:pk>/edit/",
        CatalogItemUpdateView.as_view(),
        name="catalog_edit",
    ),
    path("units/", UnitListView.as_view(), name="unit_list"),
    path("units/new/", UnitCreateView.as_view(), name="unit_create"),
    path("units/<int:pk>/edit/", UnitUpdateView.as_view(), name="unit_edit"),
    path("units/<int:pk>/delete/", UnitDeleteView.as_view(), name="unit_delete"),
]
