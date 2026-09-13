from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import NoReverseMatch, reverse


def htmx_redirect(url: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


def _login_path() -> str:
    """Resolve ``settings.LOGIN_URL`` to a path (it may be a URL name)."""
    try:
        return str(reverse(settings.LOGIN_URL))
    except (NoReverseMatch, TypeError):
        return str(settings.LOGIN_URL)


class HTMXLoginRedirectMiddleware:
    """Convert login redirects into HX-Redirect responses for HTMX requests.

    When a session expires mid-SPA-navigation, ``LoginRequiredMixin`` returns a
    302 to the login page. An HTMX request cannot follow it usefully, so this
    middleware answers with ``204 + HX-Redirect`` — htmx then performs a full
    page load, preserving the ``?next=`` query string. Redirects to any other
    URL pass through untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if (
            request.headers.get("HX-Request") == "true"
            and isinstance(response, HttpResponseRedirect)
            and urlsplit(response.url).path == _login_path()
        ):
            return htmx_redirect(response.url)
        return response
