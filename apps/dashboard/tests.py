from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .views import ComponentGalleryView

User = get_user_model()


class HomeRouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_anonymous_home_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('dashboard:home')}")

    def test_home_renders_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shell.html")
        self.assertContains(response, "Overview")

    def test_shell_renders_theme_and_sidebar_toggles(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "data-sidebar-toggle")
        self.assertContains(response, 'data-theme="light"')

    def test_sidebar_lists_all_sections(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard:home"))
        for label in ("Overview", "Workspace", "AI", "Management"):
            self.assertContains(response, label)


class GalleryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_gallery_renders_via_request_factory(self):
        request = RequestFactory().get("/ui/")
        request.user = self.user
        response = ComponentGalleryView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        content = response.render().content.decode()
        self.assertIn("Component gallery", content)
        self.assertIn("btn-primary", content)
