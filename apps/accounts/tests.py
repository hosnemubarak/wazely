from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from allauth.account.models import EmailAddress

User = get_user_model()


class SignupFlowTests(TestCase):
    def test_signup_page_renders(self):
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, "wazely-theme")

    def test_signup_creates_unverified_user_and_sends_email(self):
        response = self.client.post(
            reverse("account_signup"),
            {"email": "user@example.com", "password1": "correct-horse-battery", "password2": "correct-horse-battery"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="user@example.com").exists())
        self.assertFalse(EmailAddress.objects.get(user__email="user@example.com").verified)
        self.assertEqual(len(mail.outbox), 1)


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")
        EmailAddress.objects.create(user=cls.user, email=cls.user.email, primary=True, verified=True)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "user@example.com", "password": "correct-horse-battery"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_invalid_login_rerenders_with_errors(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "user@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "error")

    def test_htmx_invalid_login_returns_partial_only(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "user@example.com", "password": "wrong"},
            headers={"HX-Request": "true", "X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/_login_form.html")
        self.assertNotContains(response, "<!DOCTYPE html>")

    def test_htmx_valid_login_returns_hx_redirect(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "user@example.com", "password": "correct-horse-battery"},
            headers={"HX-Request": "true", "X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:home"))

    def test_htmx_logout_returns_hx_redirect(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("account_logout"),
            headers={"HX-Request": "true", "X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("account_login"))


class DashboardAccessTests(TestCase):
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
        self.assertContains(response, "Overview")
        self.assertContains(response, "data-theme-toggle")
        self.assertContains(response, 'data-theme="light"')


class PasswordResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")
        EmailAddress.objects.create(user=cls.user, email=cls.user.email, primary=True, verified=True)

    def test_reset_request_sends_email(self):
        response = self.client.post(reverse("account_reset_password"), {"email": "user@example.com"})
        self.assertRedirects(response, reverse("account_reset_password_done"))
        self.assertEqual(len(mail.outbox), 1)
