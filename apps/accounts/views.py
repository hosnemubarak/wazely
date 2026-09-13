import json
from urllib.parse import urlsplit

from allauth.account import views as account_views
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.urls import Resolver404, resolve


def htmx_redirect(url: str) -> HttpResponse:
    """Answer with a 204 + HX-Redirect: htmx performs a full page load."""
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


def htmx_location(url: str, target: str) -> HttpResponse:
    """Answer with a 204 + HX-Location: htmx GETs the URL and swaps it in place.

    htmx pushes the URL into history, so in-shell auth navigation behaves like
    a real page change without a full document reload.
    """
    response = HttpResponse(status=204)
    response["HX-Location"] = json.dumps({"path": url, "target": target, "swap": "innerHTML"})
    return response


# Account pages rendered inside the auth shell (templates/account/base.html).
AUTH_SHELL_URL_NAMES = frozenset(
    {
        "account_login",
        "account_signup",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
        "account_email_verification_sent",
        "account_confirm_email",
        "account_inactive",
        "account_logout",
    }
)


def is_auth_shell_url(url: str) -> bool:
    """Whether a redirect target is an auth page that shares the auth shell."""
    try:
        match = resolve(urlsplit(url).path)
    except Resolver404:
        return False
    return match.url_name in AUTH_SHELL_URL_NAMES


class HTMXAccountMixin:
    """Serve partial templates and HTMX redirect responses for HTMX requests.

    - POST renders ``htmx_template`` (the form partial) so htmx swaps validation
      errors over ``#auth-form``. Views without a form partial fall back to the
      content partial.
    - GET (in-shell navigation) renders ``htmx_content_template`` so htmx swaps
      the page content over ``#auth-content``.
    - Redirects become ``HX-Redirect`` (full page load). When
      ``htmx_redirect_in_shell`` is set and the target is another auth page,
      they become ``HX-Location`` instead, keeping the auth shell in place.

    Every subclass must declare ``htmx_content_template``: without it an HTMX
    request would render a whole document into ``#auth-content``.
    """

    htmx_template: str = ""
    htmx_content_template: str = ""
    htmx_content_target: str = "#auth-content"
    htmx_redirect_in_shell: bool = False

    def is_htmx(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def get_template_names(self) -> list[str]:
        if self.is_htmx():
            if self.request.method == "POST" and self.htmx_template:
                return [self.htmx_template]
            if self.htmx_content_template:
                return [self.htmx_content_template]
        return super().get_template_names()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        try:
            response = super().dispatch(request, *args, **kwargs)
        except ImmediateHttpResponse as exc:
            response = exc.response
        if self.is_htmx() and isinstance(response, HttpResponseRedirect):
            if self.htmx_redirect_in_shell and is_auth_shell_url(response.url):
                return htmx_location(response.url, target=self.htmx_content_target)
            return htmx_redirect(response.url)
        return response


class LoginView(HTMXAccountMixin, account_views.LoginView):
    htmx_template = "account/_login_form.html"
    htmx_content_template = "account/_login_content.html"


class SignupView(HTMXAccountMixin, account_views.SignupView):
    htmx_template = "account/_signup_form.html"
    htmx_content_template = "account/_signup_content.html"
    htmx_redirect_in_shell = True


class LogoutView(HTMXAccountMixin, account_views.LogoutView):
    htmx_content_template = "account/_logout_content.html"


class ConfirmEmailView(HTMXAccountMixin, account_views.ConfirmEmailView):
    htmx_content_template = "account/_email_confirm_content.html"


class AccountInactiveView(HTMXAccountMixin, account_views.AccountInactiveView):
    htmx_content_template = "account/_account_inactive_content.html"


class PasswordResetView(HTMXAccountMixin, account_views.PasswordResetView):
    htmx_template = "account/_password_reset_form.html"
    htmx_content_template = "account/_password_reset_content.html"
    htmx_redirect_in_shell = True


class PasswordResetDoneView(HTMXAccountMixin, account_views.PasswordResetDoneView):
    htmx_content_template = "account/_password_reset_done_content.html"


class PasswordResetFromKeyView(HTMXAccountMixin, account_views.PasswordResetFromKeyView):
    htmx_template = "account/_password_reset_from_key_form.html"
    htmx_content_template = "account/_password_reset_from_key_content.html"
    htmx_redirect_in_shell = True


class PasswordResetFromKeyDoneView(HTMXAccountMixin, account_views.PasswordResetFromKeyDoneView):
    htmx_content_template = "account/_password_reset_from_key_done_content.html"


class EmailVerificationSentView(HTMXAccountMixin, account_views.EmailVerificationSentView):
    htmx_content_template = "account/_verification_sent_content.html"
