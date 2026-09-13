from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.mixins import SPAContentMixin


class TeamView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    template_name = "organizations/team.html"


class SettingsView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    template_name = "organizations/settings.html"
