from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("team/", views.TeamView.as_view(), name="team"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
]
