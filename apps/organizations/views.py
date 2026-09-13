from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class TeamView(LoginRequiredMixin, TemplateView):
    template_name = "organizations/team.html"


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "organizations/settings.html"
