class SPAContentMixin:
    """Render the app's content partial for HTMX requests, full page otherwise.

    The partial is derived from ``template_name``: ``<app>/index.html`` becomes
    ``<app>/_content.html``, any other ``<app>/<page>.html`` becomes
    ``<app>/_<page>_content.html``. Set ``partial_template_name`` to override.
    """

    partial_template_name: str = ""

    def is_htmx(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def get_template_names(self) -> list[str]:
        if not self.is_htmx():
            return super().get_template_names()
        if self.partial_template_name:
            return [self.partial_template_name]
        return [self._derive_partial_name(name) for name in super().get_template_names()]

    @staticmethod
    def _derive_partial_name(template_name: str) -> str:
        directory, _, filename = template_name.rpartition("/")
        stem = filename.removesuffix(".html")
        partial_stem = "_content" if stem == "index" else f"_{stem}_content"
        prefix = f"{directory}/" if directory else ""
        return f"{prefix}{partial_stem}.html"
