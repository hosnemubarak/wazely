import json
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import mail
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.test import TestCase
from django.urls import reverse

from allauth.account.models import EmailAddress, EmailConfirmationHMAC

from . import views as account_views
from .forms import LoginForm, ResetPasswordKeyForm
from .views import HTMXAccountMixin, is_auth_shell_url

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
            {
                "email": "user@example.com",
                "password1": "correct-horse-battery",
                "password2": "correct-horse-battery",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="user@example.com").exists())
        self.assertFalse(EmailAddress.objects.get(user__email="user@example.com").verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "mismatch@example.com",
                "password1": "correct-horse-battery",
                "password2": "different-horse-battery",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.filter(email="mismatch@example.com").exists())


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

    def test_login_form_carries_the_next_redirect(self):
        response = self.client.get(f"{reverse('account_login')}?next=/conversations/")
        self.assertContains(response, '<input type="hidden" name="next" value="/conversations/">')

    def test_htmx_login_preserves_next(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": self.user.email, "password": "correct-horse-battery", "next": "/conversations/"},
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers.get("HX-Redirect"), "/conversations/")

    def test_remember_checkbox_renders_inline(self):
        content = self.client.get(reverse("account_login")).content.decode()
        self.assertRegex(
            content,
            r'<div class="form-field">\s*<div class="flex items-center gap-2">\s*<input type="checkbox" name="remember"',
        )


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


class PasswordValidationTests(TestCase):
    """Django's built-in validators plus the repeated/sequential guard."""

    def test_strong_passwords_are_accepted(self):
        for password in ("correct-horse-battery", "Tr0ub4dor&3xample"):
            with self.subTest(password=password):
                validate_password(password)

    def test_repeated_character_password_is_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_password("aaaaaaaa")
        self.assertIn("password_repeated", {error.code for error in ctx.exception.error_list})

    def test_sequential_passwords_are_rejected(self):
        for password in ("abcdefgh", "87654321"):
            with self.subTest(password=password):
                with self.assertRaises(ValidationError) as ctx:
                    validate_password(password)
                self.assertIn("password_sequential", {error.code for error in ctx.exception.error_list})

    def test_signup_rejects_weak_passwords(self):
        for password in ("password", "12345678", "aaaaaaaa"):
            with self.subTest(password=password):
                response = self.client.post(
                    reverse("account_signup"),
                    {"email": "weak@example.com", "password1": password, "password2": password},
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("password1", response.context["form"].errors)
                self.assertFalse(User.objects.filter(email="weak@example.com").exists())

    def test_signup_accepts_a_strong_password(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "strong@example.com",
                "password1": "correct-horse-battery",
                "password2": "correct-horse-battery",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="strong@example.com").exists())

    def test_requirements_render_as_one_summary_line(self):
        response = self.client.get(reverse("account_signup"))
        self.assertRegex(
            response.content.decode(),
            r'<div class="form-help[^"]*" id="id_password1_helptext">[^<]*8 characters[^<]*</div>',
        )
        self.assertNotContains(response, "must contain at least 8 characters")

    def test_multiple_errors_render_one_idempotent_container(self):
        response = self.client.post(
            reverse("account_signup"),
            {"email": "multi@example.com", "password1": "12345678", "password2": "12345678"},
        )
        content = response.content.decode()
        self.assertEqual(content.count('id="id_password1_error"'), 1)
        container = re.search(
            r'<ul class="field-error[^"]*" id="id_password1_error">(.*?)</ul>', content, re.S
        )
        self.assertIsNotNone(container)
        self.assertGreaterEqual(container.group(1).count("<li>"), 2)


class PasswordMaskingTests(TestCase):
    """Password fields render masked with no reveal affordance anywhere."""

    def test_no_reveal_toggle_is_rendered(self):
        for name in ("account_login", "account_signup"):
            with self.subTest(route=name):
                content = self.client.get(reverse(name)).content.decode()
                self.assertNotIn("wzPassword", content)
                self.assertNotIn("input-with-toggle", content)
                self.assertNotIn('aria-label="Show password"', content)
                self.assertNotIn('aria-controls="id_password', content)

    def test_password_inputs_are_masked_by_default(self):
        for name, expected in (("account_login", 1), ("account_signup", 2)):
            with self.subTest(route=name):
                content = self.client.get(reverse(name)).content.decode()
                masked = re.findall(r'<input type="password" name="password\d?"', content)
                self.assertEqual(len(masked), expected)
                self.assertNotRegex(content, r'<input type="text" name="password')

    def test_native_reveal_eyes_are_hidden_by_the_built_css(self):
        built_css = (settings.BASE_DIR / "static" / "css" / "app.css").read_text(encoding="utf-8")
        self.assertIn("::-ms-reveal", built_css, "Edge's native reveal eye must stay hidden")
        self.assertIn("::-ms-clear", built_css)
        self.assertNotIn(".input-with-toggle", built_css)

    def test_password_is_never_echoed_back_after_a_failed_login(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "echo@example.com", "password": "SuperSecretValue123"},
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "SuperSecretValue123")


class AccountFormsTests(TestCase):
    """The form overrides registered via ACCOUNT_FORMS."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("forms@example.com", "correct-horse-battery")

    def test_login_form_flags_the_forgot_password_link_and_drops_help_text(self):
        form = LoginForm()
        self.assertTrue(form.fields["password"].show_forgot_password_link)
        self.assertEqual(form.fields["password"].help_text, "")

    def test_reset_key_form_asks_for_the_password_once_with_summary_help(self):
        form = ResetPasswordKeyForm(user=self.user, temp_key="abc")
        self.assertNotIn("password2", form.fields)
        self.assertIn("8 characters", form.fields["password1"].help_text)
        self.assertNotIn("placeholder", form.fields["password1"].widget.attrs)

    def test_reset_key_password_field_is_masked(self):
        form = ResetPasswordKeyForm(user=self.user, temp_key="abc")
        self.assertEqual(form.fields["password1"].widget.input_type, "password")


class AccountFormPresentationTests(TestCase):
    """One reset link, example placeholders, one password field, one help line."""

    def test_login_shows_one_forgot_password_link_on_the_password_label_row(self):
        content = self.client.get(reverse("account_login")).content.decode()
        self.assertEqual(content.count("Forgot password?"), 1)
        self.assertEqual(content.count("Forgot your password?"), 0)
        self.assertRegex(
            content,
            r'<label for="id_password"[^>]*>Password</label>\s*'
            r'<a href="/accounts/password/reset/" class="auth-link text-xs"',
        )

    def test_email_fields_use_an_example_placeholder(self):
        for name in ("account_login", "account_signup", "account_reset_password"):
            with self.subTest(route=name):
                content = self.client.get(reverse(name)).content.decode()
                self.assertIn('placeholder="you@example.com"', content)
                self.assertNotIn('placeholder="Email address"', content)

    def test_password_fields_have_no_placeholder(self):
        for name in ("account_login", "account_signup"):
            with self.subTest(route=name):
                content = self.client.get(reverse(name)).content.decode()
                self.assertNotIn('placeholder="Password"', content)
                self.assertNotIn('placeholder="Password (again)"', content)

    def test_signup_asks_to_confirm_the_password(self):
        content = self.client.get(reverse("account_signup")).content.decode()
        self.assertIn('id="id_password2"', content)
        self.assertIn("Password (again)", content)

    def test_fields_stack_with_body_size_labels(self):
        content = self.client.get(reverse("account_login")).content.decode()
        self.assertIn('<div class="space-y-5">', content)
        self.assertRegex(
            content,
            r'<label for="id_login" class="text-sm font-medium text-slate-700 dark:text-slate-300">',
        )
        error_page = self.client.post(
            reverse("account_signup"),
            {"email": "size@example.com", "password1": "12345678", "password2": "12345678"},
        ).content.decode()
        self.assertRegex(error_page, r'<ul class="field-error[^"]*text-sm')


class AuthSPANavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")
        EmailAddress.objects.create(user=cls.user, email=cls.user.email, primary=True, verified=True)

    SPA_PAGES = [
        ("account_login", "account/_login_content.html", "Log in · Wazely"),
        ("account_signup", "account/_signup_content.html", "Sign up · Wazely"),
        ("account_reset_password", "account/_password_reset_content.html", "Reset password · Wazely"),
        ("account_reset_password_done", "account/_password_reset_done_content.html", "Password reset sent · Wazely"),
        ("account_email_verification_sent", "account/_verification_sent_content.html", "Verify your email · Wazely"),
        (
            "account_reset_password_from_key_done",
            "account/_password_reset_from_key_done_content.html",
            "Password changed · Wazely",
        ),
    ]

    def test_htmx_get_renders_the_content_partial(self):
        for name, template, title in self.SPA_PAGES:
            with self.subTest(route=name):
                response = self.client.get(reverse(name), headers={"HX-Request": "true"})
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.assertContains(response, f'data-page-title="{title}"')
                self.assertNotContains(response, "<!DOCTYPE html>")

    def test_plain_get_renders_the_full_auth_shell(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "<!DOCTYPE html>")
        self.assertContains(response, 'id="auth-content"')
        self.assertContains(response, "hx-history-elt")

    def test_navigation_links_swap_the_auth_content(self):
        content = self.client.get(reverse("account_login")).content.decode()
        for name in ("account_signup", "account_reset_password"):
            self.assertIn(f'hx-get="{reverse(name)}"', content)
        self.assertIn('hx-target="#auth-content"', content)
        self.assertIn('hx-push-url="true"', content)

    def test_htmx_login_success_redirects_to_the_dashboard(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": self.user.email, "password": "correct-horse-battery"},
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:home"))
        self.assertFalse(response.has_header("HX-Location"))

    def test_htmx_signup_success_stays_in_the_auth_shell(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "new@example.com",
                "password1": "correct-horse-battery",
                "password2": "correct-horse-battery",
            },
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 204)
        location = json.loads(response.headers["HX-Location"])
        self.assertEqual(location["path"], reverse("account_email_verification_sent"))
        self.assertEqual(location["target"], "#auth-content")
        self.assertFalse(response.has_header("HX-Redirect"))

    def test_htmx_password_reset_success_stays_in_the_auth_shell(self):
        response = self.client.post(
            reverse("account_reset_password"),
            {"email": self.user.email},
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 204)
        location = json.loads(response.headers["HX-Location"])
        self.assertEqual(location["path"], reverse("account_reset_password_done"))
        self.assertEqual(location["target"], "#auth-content")

    def test_is_auth_shell_url_recognises_auth_pages_only(self):
        self.assertTrue(is_auth_shell_url(reverse("account_login")))
        self.assertTrue(is_auth_shell_url(f"{reverse('account_login')}?next=/"))
        self.assertFalse(is_auth_shell_url(reverse("dashboard:home")))
        self.assertFalse(is_auth_shell_url("/definitely-not-a-route/"))

    def test_every_auth_page_serves_a_content_partial(self):
        email_address = EmailAddress.objects.create(
            user=self.user, email="confirm-spa@example.com", primary=False, verified=False
        )
        self.client.force_login(self.user)
        urls = [
            "/accounts/password/reset/key/abc-def/",  # token-fail state
            reverse("account_confirm_email", args=[EmailConfirmationHMAC(email_address).key]),
            reverse("account_inactive"),
            reverse("account_logout"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, headers={"HX-Request": "true"})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-page-title="')
                self.assertNotContains(response, "<!DOCTYPE html>")
                self.assertNotContains(response, "Wazely brings your organization")


class AuthPageConsistencyTests(TestCase):
    """Login, signup, reset and the terminal pages share one design language."""

    PAGES = [
        reverse("account_login"),
        reverse("account_signup"),
        reverse("account_reset_password"),
        reverse("account_reset_password_done"),
        reverse("account_email_verification_sent"),
        reverse("account_reset_password_from_key_done"),
        reverse("account_inactive"),
        "/accounts/password/reset/key/abc-def/",  # token-fail state
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("consistency@example.com", "correct-horse-battery")

    def test_pages_share_the_auth_shell_and_language(self):
        for url in self.PAGES:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "account/base.html")
                self.assertContains(response, 'id="auth-content"')
                self.assertContains(response, "auth-title")
                self.assertEqual(response.content.decode().count("<h1"), 1)

    def test_every_auth_form_uses_the_shared_form_shell(self):
        for url in self.PAGES:
            with self.subTest(url=url):
                content = self.client.get(url).content.decode()
                if "<form" in content:
                    self.assertIn('id="auth-form"', content)

    def test_logout_page_shares_the_auth_shell_and_language(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("account_logout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, 'id="auth-content"')
        self.assertContains(response, "auth-title")
        self.assertIn('id="auth-form"', response.content.decode())

    def test_email_confirm_page_shares_the_auth_shell_and_language(self):
        email_address = EmailAddress.objects.create(
            user=self.user, email="confirm@example.com", primary=False, verified=False
        )
        key = EmailConfirmationHMAC(email_address).key
        response = self.client.get(reverse("account_confirm_email", args=[key]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "auth-title")
        self.assertContains(response, 'id="auth-form"')
        self.assertEqual(response.content.decode().count("<h1"), 1)
        self.assert_title_matches(reverse("account_confirm_email", args=[key]))

    def test_titles_match_between_full_page_and_content_partial(self):
        for url in self.PAGES:
            with self.subTest(url=url):
                self.assert_title_matches(url)

    def test_logout_title_matches_between_full_page_and_content_partial(self):
        self.client.force_login(self.user)
        self.assert_title_matches(reverse("account_logout"))

    def assert_title_matches(self, url):
        """`{% block title %}` and `data-page-title` must stay identical:
        app.js rewrites document.title from the partial on in-shell swaps."""
        full = self.client.get(url).content.decode()
        partial = self.client.get(url, headers={"HX-Request": "true"}).content.decode()
        document_title = re.search(r"<title>(.*?)</title>", full)
        page_title = re.search(r'data-page-title="([^"]+)"', partial)
        self.assertIsNotNone(document_title, "missing <title>")
        self.assertIsNotNone(page_title, "missing data-page-title")
        self.assertEqual(document_title.group(1), page_title.group(1))


class HTMXAccountMixinContractTests(TestCase):
    def test_every_wrapped_view_declares_existing_templates(self):
        wrapped = [
            obj
            for obj in vars(account_views).values()
            if isinstance(obj, type) and issubclass(obj, HTMXAccountMixin) and obj is not HTMXAccountMixin
        ]
        self.assertTrue(wrapped)
        for view_class in wrapped:
            with self.subTest(view=view_class.__name__):
                self.assertTrue(
                    view_class.htmx_content_template,
                    "every wrapper needs a content partial or an HTMX GET swaps a whole document",
                )
                get_template(view_class.htmx_content_template)
                if view_class.htmx_template:
                    get_template(view_class.htmx_template)



