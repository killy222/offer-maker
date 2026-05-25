from django.urls import path

from .views import (
    ClientCompanyCreateView,
    ClientCompanyDeleteView,
    ClientCompanyListView,
    ClientCompanyUpdateView,
)

urlpatterns = [
    path("clients/", ClientCompanyListView.as_view(), name="client_list"),
    path("clients/new/", ClientCompanyCreateView.as_view(), name="client_create"),
    path(
        "clients/<int:pk>/delete/",
        ClientCompanyDeleteView.as_view(),
        name="client_delete",
    ),
    path(
        "clients/<int:pk>/edit/",
        ClientCompanyUpdateView.as_view(),
        name="client_edit",
    ),
]
