from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_anonymous_team_redirects_to_login(self):
        response = self.client.get(reverse("organizations:team"))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('organizations:team')}")

    def test_authenticated_team_renders_shell(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:team"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shell.html")
        self.assertContains(response, "Team")

    def test_anonymous_settings_redirects_to_login(self):
        response = self.client.get(reverse("organizations:settings"))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('organizations:settings')}")

    def test_authenticated_settings_renders_shell(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shell.html")
        self.assertContains(response, "Settings")
