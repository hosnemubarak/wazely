from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.constants import SUCCESS
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic import TemplateView

from .mixins import SPAContentMixin

User = get_user_model()


class SPAIndexView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    """Test double mirroring the project's dashboard views."""

    template_name = "conversations/index.html"


class SPAContentMixinTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_partial_name_derivation(self):
        self.assertEqual(
            SPAContentMixin._derive_partial_name("conversations/index.html"),
            "conversations/_content.html",
        )
        self.assertEqual(
            SPAContentMixin._derive_partial_name("organizations/team.html"),
            "organizations/_team_content.html",
        )

    def test_htmx_request_renders_content_partial(self):
        request = RequestFactory().get("/conversations/", headers={"HX-Request": "true"})
        request.user = self.user
        response = SPAIndexView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        content = response.render().content.decode()
        self.assertIn('data-page-title="Conversations · Wazely"', content)
        self.assertNotIn("<!DOCTYPE html>", content)
        self.assertNotIn("main-shell", content)

    def test_plain_request_renders_full_page(self):
        request = RequestFactory().get("/conversations/")
        request.user = self.user
        response = SPAIndexView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        content = response.render().content.decode()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("main-shell", content)


class HTMXLoginRedirectMiddlewareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    def test_anonymous_htmx_get_returns_hx_redirect(self):
        htmx_response = self.client.get(reverse("conversations:index"), headers={"HX-Request": "true"})
        plain_response = self.client.get(reverse("conversations:index"))
        self.assertEqual(htmx_response.status_code, 204)
        self.assertEqual(htmx_response.headers.get("HX-Redirect"), plain_response["Location"])
        self.assertIn("next=", plain_response["Location"])

    def test_anonymous_plain_get_still_redirects(self):
        response = self.client.get(reverse("conversations:index"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"{reverse('account_login')}?next={reverse('conversations:index')}")

    def test_logged_in_htmx_get_unaffected(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("conversations:index"), headers={"HX-Request": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.has_header("HX-Redirect"))


class OOBToastTests(TestCase):
    def test_oob_partial_renders_toasts_with_oob_swap_for_htmx(self):
        request = RequestFactory().get("/conversations/", headers={"HX-Request": "true"})
        html = render_to_string(
            "partials/_toasts_oob.html",
            {"messages": [Message(SUCCESS, "Saved.", "")]},
            request=request,
        )
        self.assertIn('hx-swap-oob="beforeend:#toast-container"', html)
        self.assertIn("Saved.", html)

    def test_oob_partial_is_empty_for_full_page_renders(self):
        request = RequestFactory().get("/conversations/")
        html = render_to_string(
            "partials/_toasts_oob.html",
            {"messages": [Message(SUCCESS, "Saved.", "")]},
            request=request,
        )
        self.assertEqual(html.strip(), "")

    def test_messages_partial_has_no_oob_attribute(self):
        request = RequestFactory().get("/")
        html = render_to_string(
            "partials/_messages.html",
            {"messages": [Message(SUCCESS, "Saved.", "")]},
            request=request,
        )
        self.assertNotIn("hx-swap-oob", html)
        self.assertIn("Saved.", html)


class SPARouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")

    routes = [
        ("dashboard:home", "dashboard/_home_content.html"),
        ("conversations:index", "conversations/_content.html"),
        ("contacts:index", "contacts/_content.html"),
        ("whatsapp:index", "whatsapp/_content.html"),
        ("agents:index", "agents/_content.html"),
        ("knowledge:index", "knowledge/_content.html"),
        ("organizations:team", "organizations/_team_content.html"),
        ("organizations:settings", "organizations/_settings_content.html"),
    ]

    def test_htmx_requests_render_content_partials(self):
        self.client.force_login(self.user)
        for name, partial in self.routes:
            with self.subTest(route=name):
                response = self.client.get(reverse(name), headers={"HX-Request": "true"})
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, partial)
                self.assertContains(response, "data-page-title")
                self.assertNotContains(response, "<!DOCTYPE html>")
                self.assertNotContains(response, "main-shell")

    def test_plain_requests_render_full_shell(self):
        self.client.force_login(self.user)
        for name, partial in self.routes:
            with self.subTest(route=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "shell.html")
                self.assertContains(response, "<!DOCTYPE html>")
