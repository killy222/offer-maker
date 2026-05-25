from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ClientCompanyForm
from .models import ClientCompany


class ClientCompanyListView(LoginRequiredMixin, ListView):
    model = ClientCompany
    context_object_name = "clients"
    template_name = "clients/client_list.html"


class ClientCompanyCreateView(LoginRequiredMixin, CreateView):
    model = ClientCompany
    form_class = ClientCompanyForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("client_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _lazy("Add client company")
        ctx["submit_label"] = _lazy("Create")
        return ctx


class ClientCompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientCompany
    form_class = ClientCompanyForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("client_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _lazy("Edit client company")
        ctx["submit_label"] = _lazy("Save")
        return ctx


class ClientCompanyDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        client = get_object_or_404(ClientCompany, pk=pk)
        name = client.name
        client.delete()
        messages.success(request, _('Client "%(name)s" was deleted.') % {"name": name})
        return HttpResponseRedirect(reverse("client_list"))
