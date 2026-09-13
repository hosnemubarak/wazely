from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.mixins import SPAContentMixin


class HomeView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"


class ComponentGalleryView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    """DEBUG-only manual QA surface for the component library."""

    template_name = "dashboard/ui_gallery.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dropdown_items"] = [
            {"label": "Overview", "url": "/"},
            {"label": "Conversations", "url": "/conversations/"},
            {"label": "Contacts", "url": "/contacts/"},
        ]
        context["table_headers"] = ["Name", "Email", "Role"]
        context["table_rows"] = [
            ["Ada Lovelace", "ada@example.com", "Owner"],
            ["Grace Hopper", "grace@example.com", "Member"],
        ]
        return context
