from allauth.account import views as account_views
from allauth.core.exceptions import ImmediateHttpResponse
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect


def htmx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


class HTMXAccountMixin:
    """Serve partial templates and HX-Redirect responses for HTMX requests."""

    htmx_template: str = ""

    def is_htmx(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def get_template_names(self) -> list[str]:
        if self.is_htmx() and self.htmx_template:
            return [self.htmx_template]
        return super().get_template_names()

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
        except ImmediateHttpResponse as exc:
            response = exc.response
        if self.is_htmx() and isinstance(response, HttpResponseRedirect):
            return htmx_redirect(response.url)
        return response


class LoginView(HTMXAccountMixin, account_views.LoginView):
    htmx_template = "account/_login_form.html"


class SignupView(HTMXAccountMixin, account_views.SignupView):
    htmx_template = "account/_signup_form.html"


class LogoutView(HTMXAccountMixin, account_views.LogoutView):
    pass


class PasswordResetView(HTMXAccountMixin, account_views.PasswordResetView):
    htmx_template = "account/_password_reset_form.html"


class PasswordResetFromKeyView(HTMXAccountMixin, account_views.PasswordResetFromKeyView):
    htmx_template = "account/_password_reset_from_key_form.html"
