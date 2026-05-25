from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import CatalogItemForm, UnitForm
from .models import CatalogItem, Unit


class CatalogItemListView(LoginRequiredMixin, ListView):
    model = CatalogItem
    context_object_name = "items"
    template_name = "products/catalog_list.html"

    def get_queryset(self):
        return super().get_queryset().select_related("unit")


class CatalogItemCreateView(LoginRequiredMixin, CreateView):
    model = CatalogItem
    form_class = CatalogItemForm
    template_name = "products/catalog_form.html"
    success_url = reverse_lazy("catalog_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Add catalog item")
        ctx["submit_label"] = _("Create")
        return ctx


class CatalogItemUpdateView(LoginRequiredMixin, UpdateView):
    model = CatalogItem
    form_class = CatalogItemForm
    template_name = "products/catalog_form.html"
    success_url = reverse_lazy("catalog_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Edit catalog item")
        ctx["submit_label"] = _("Save")
        return ctx


class CatalogItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(CatalogItem, pk=pk)
        name = item.name
        try:
            item.delete()
        except ProtectedError:
            messages.error(
                request,
                _('Cannot delete "%(name)s" because it is used on one or more offers.')
                % {"name": name},
            )
            return HttpResponseRedirect(reverse("catalog_list"))
        messages.success(request, _('Catalog item "%(name)s" was deleted.') % {"name": name})
        return HttpResponseRedirect(reverse("catalog_list"))


class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    context_object_name = "units"
    template_name = "products/unit_list.html"


class UnitCreateView(LoginRequiredMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = "products/unit_form.html"
    success_url = reverse_lazy("unit_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Add unit")
        ctx["submit_label"] = _("Create")
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Unit "%(name)s" was created.') % {"name": self.object.label_bg},
        )
        return response


class UnitUpdateView(LoginRequiredMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = "products/unit_form.html"
    success_url = reverse_lazy("unit_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Edit unit")
        ctx["submit_label"] = _("Save")
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Unit "%(name)s" was updated.') % {"name": self.object.label_bg},
        )
        return response


class UnitDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)
        name = unit.label_bg
        try:
            unit.delete()
        except ProtectedError:
            messages.error(
                request,
                _('Cannot delete unit "%(name)s" because it is used by one or more catalog items.')
                % {"name": name},
            )
            return HttpResponseRedirect(reverse("unit_list"))
        messages.success(request, _('Unit "%(name)s" was deleted.') % {"name": name})
        return HttpResponseRedirect(reverse("unit_list"))
