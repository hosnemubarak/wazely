from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("conversations/", include("apps.conversations.urls")),
    path("contacts/", include("apps.contacts.urls")),
    path("whatsapp/", include("apps.whatsapp.urls")),
    path("agents/", include("apps.agents.urls")),
    path("knowledge/", include("apps.knowledge.urls")),
    path("", include("apps.organizations.urls")),
]

if settings.DEBUG:
    from apps.dashboard import views as dashboard_views

    urlpatterns += [
        path("ui/", dashboard_views.ComponentGalleryView.as_view(), name="ui_gallery"),
    ]
