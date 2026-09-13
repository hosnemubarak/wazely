from allauth.account.adapter import DefaultAccountAdapter
from django.http import HttpRequest


class AccountAdapter(DefaultAccountAdapter):
    """Serve HTMX requests as HTML; allauth's JSON AJAX protocol is unused."""

    def is_ajax(self, request: HttpRequest) -> bool:
        return False
