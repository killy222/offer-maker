from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from .forms import CompanyProfileForm
from .models import CompanyProfile


class CompanyProfileView(LoginRequiredMixin, View):
    template_name = "company/company_profile.html"

    def get(self, request):
        profile = CompanyProfile.get_solo()
        form = CompanyProfileForm(instance=profile)
        return render(
            request,
            self.template_name,
            {"form": form, "company_profile": profile},
        )

    def post(self, request):
        profile = CompanyProfile.get_solo()
        form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("company_profile"))
        return render(
            request,
            self.template_name,
            {"form": form, "company_profile": profile},
        )
