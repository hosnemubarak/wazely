from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class IndexRouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("contacts:index"))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('contacts:index')}")

    def test_authenticated_renders_shell(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("contacts:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shell.html")
        self.assertContains(response, "Contacts")
