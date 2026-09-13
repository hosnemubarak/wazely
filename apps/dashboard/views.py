from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"


class ComponentGalleryView(LoginRequiredMixin, TemplateView):
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
