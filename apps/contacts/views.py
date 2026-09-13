from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.mixins import SPAContentMixin


class IndexView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    template_name = "contacts/index.html"
