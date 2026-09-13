# Wazely HTMX SPA Architecture

Convert the dashboard from full-page navigation to a server-rendered HTMX SPA:
persistent shell (sidebar + navbar + toast container), only `#main-content`
swaps, browser history works, and the pattern becomes a project-wide rule.

No React/Vue/JS SPA. Django keeps rendering everything. No URL or model changes.

## Current state (verified)

- 8 dashboard routes are `LoginRequiredMixin + TemplateView` rendering full
  `shell.html` pages (`apps/*/views.py`). Sidebar links are plain `<a href>`.
- `templates/shell.html` wraps sidebar + navbar + `<main id="main-content">`
  with blocks `page_header`/`breadcrumb`/`page_title`/`page_actions`/`content`.
- Auth already follows the partial philosophy: `HTMXAccountMixin`
  (`apps/accounts/views.py`) renders `account/_*.html` partials for `HX-Request`
  and converts redirects to `HX-Redirect`. Forms target `#auth-form`.
- `static/js/app.js` holds theme/sidebar/toast behavior + the
  `htmx:afterSwap → Alpine.initTree` hook. Toasts render server-side into
  `#toast-container` on full pages only.
- Skills: `htmx-patterns` (partial-response fundamentals), `wazely-ui`
  (design system). Both must be updated, not duplicated.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Partial strategy | Server-side `HX-Request` detection per view | User's flow diagram specifies it; `htmx-patterns` skill mandates partials; smaller payloads than hx-boost/hx-select |
| Shared code home | New `apps/core` (mixins + middleware, no models) | AGENTS.md forbids cross-app imports; `core` is the standard Django home for cross-cutting infra |
| Active nav state | Client-side sync in `app.js` (move `aria-current` by `location.pathname`) | Sidebar isn't re-rendered on swaps; styling already keys off the attribute; no response bloat |
| Auth failures in HTMX | Middleware converts login redirects to `204 + HX-Redirect` | Catches all views (incl. future function views) once; mirrors the existing `HTMXAccountMixin` convention |
| Toasts over HTMX | OOB swap (`hx-swap-oob="beforeend:#toast-container"`) in partial responses | Server-rendered, appends without killing existing toasts, no JS event plumbing |
| Page title | `data-page-title` attr on partial root + `app.js` sets `document.title`; htmx history cache restores titles on back/forward | htmx doesn't read titles from partial bodies |
| Loading indicator | One global top progress bar (delayed ~200ms) in `app.js`, not per-link spinners | Predictable, no flicker on fast responses, respects `prefers-reduced-motion` |
| Auth pages | Keep as-is (HTMX form swaps + `HX-Redirect`); full navigation between auth pages stays | Per requirement: don't force HTMX where browser nav is appropriate |
| `/ui/` gallery | Joins the same SPA pattern | Uniform mixin; zero special cases |

## Step 1 — `apps/core` (shared infrastructure)

1. Create `apps/core/` package (`__init__.py`, `apps.py`, `mixins.py`,
   `middleware.py`), register `apps.core` in `INSTALLED_APPS`. No models.
2. `SPAContentMixin`:

```python
class SPAContentMixin:
    """Render the app's content partial for HTMX requests, full page otherwise."""

    partial_template_name = ""  # defaults to template_name with _content.html

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return [self.partial_template_name or self._derive_partial_name()]
        return super().get_template_names()
```

   Derivation: `<app>/index.html` → `<app>/_content.html` (explicit override
   via `partial_template_name` wins).
3. `HTMXLoginRedirectMiddleware` in `apps/core/middleware.py`: if
   `HX-Request == "true"` and response is a redirect whose target resolves to
   the login URL, return `204` with `HX-Redirect: <original Location>` (keeps
   the `?next=` param). Register in `MIDDLEWARE` after `AccountMiddleware`.
   Only converts redirects to the login URL — all other redirects pass through.

## Step 2 — Template restructure

1. `templates/shell.html`: `<main id="main-content">` gains `hx-history-elt`
   and keeps only `{% block content %}`. The `page_header`/`breadcrumb`/
   `page_title`/`page_actions` blocks move out of the shell — they must swap
   with the content (blocks don't propagate through includes; verified).
2. New `templates/components/_page_header.html`: title
   (`text-2xl font-semibold tracking-tight`, `tabindex="-1"` for SPA focus),
   optional breadcrumb, optional actions slot — same markup the shell had.
3. Per app (8 pages + gallery): split into
   - `apps/<app>/templates/<app>/_content.html` — root element carries
     `data-page-title="… · Wazely"`, includes `_page_header.html`, then the
     page body, then `{% include "partials/_toasts_oob.html" %}`
   - `index.html` — `{% extends "shell.html" %}`, `{% block title %}` +
     `{% block content %}{% include "<app>/_content.html" %}{% endblock %}`
   Title strings appear in both files — keep them in sync (noted in skill).
4. `templates/partials/_toasts_oob.html`: for each message, renders the toast
   component with an OOB hook. Extend `components/_toast.html` with an optional
   `oob` variable that emits `hx-swap-oob="beforeend:#toast-container"` on the
   root div (keeps single-source toast markup; `_messages.html` passes nothing
   and is unchanged).

## Step 3 — SPA views

Each placeholder view becomes:

```python
class IndexView(SPAContentMixin, LoginRequiredMixin, TemplateView):
    template_name = "conversations/index.html"
```

Apply to: dashboard `HomeView` + `ComponentGalleryView`, conversations,
contacts, whatsapp, agents, knowledge, organizations team/settings. MRO keeps
`SPAContentMixin` first so `get_template_names` intercepts.

## Step 4 — SPA navigation markup

1. `partials/_sidebar.html`: all nav links and the brand link gain
   `hx-get="{{ url }}" hx-target="#main-content"` `hx-swap="innerHTML show:window:top"`
   `hx-push-url="true"`. Keep the `href` (progressive enhancement, middle-click,
   copy-link). Add `@click="$store.ui.drawerOpen = false"` so mobile drawer
   closes on navigation. Server-side `aria-current` stays for full renders.
2. `partials/_navbar.html`: user-menu Settings link gets the same SPA attrs.
   Logout stays `hx-post` (already returns `HX-Redirect`).
3. No `hx-boost` anywhere — explicit `hx-get` only.

## Step 5 — `app.js` additions

1. **Active nav sync**: on `htmx:afterSwap` (covers history restores), move
   `aria-current="page"` to the sidebar link matching `location.pathname`.
2. **Title**: on `htmx:afterSwap` for `#main-content`, set `document.title`
   from the swapped root's `data-page-title`.
3. **Focus**: after a content swap, focus the new `h1` (`tabindex="-1"`) so
   keyboard/screen-reader users land on the new page; skip on initial load.
4. **Loading bar**: `htmx:beforeRequest` starts a ~200ms-delayed thin top
   progress bar; `htmx:afterRequest`/`htmx:responseError` hides it. CSS in
   `app.src.css` (`.htmx-progress`), indeterminate animation, hidden under
   `prefers-reduced-motion`.
5. **Error toast**: `htmx:responseError` appends an error toast to
   `#toast-container` ("Something went wrong. Please try again.").
6. **Reduced-motion OOB toasts**: extend the existing 5s reduced-motion
   auto-dismiss to also run for toasts inserted by `htmx:afterSwap` OOB
   content (mark handled toasts with a data attribute).
7. Existing behaviors (theme, sidebar collapse, drawer, password toggle,
   Alpine re-init hook) unchanged.

## Step 6 — Auth

No behavioral change required — form partials, `#auth-form` swaps,
`HX-Redirect` on success, and the password toggle after swap already work.
The middleware from Step 1 covers session-expiry during SPA navigation.
Verify manually; do not restructure auth pages.

## Step 7 — Docs and agent rules

1. `.kilo/skill/htmx-patterns/SKILL.md`: add an **"SPA shell pattern"**
   section — persistent shell contract, `SPAContentMixin`, nav link attrs
   (`hx-get`/`hx-target`/`hx-swap`/`hx-push-url` + `hx-history-elt`),
   OOB toasts, login-redirect middleware, active-nav/title/focus sync, when
   NOT to use HTMX (auth page transitions, external links, downloads). Extend
   frontmatter triggers: SPA, single page application, navigation, history.
2. `.kilo/skill/wazely-ui/SKILL.md`: update Layouts section — shell carries
   `hx-history-elt`, page content lives in `_content.html` partials with
   `data-page-title`, `_page_header.html` component contract, progress bar,
   title-sync rule.
3. `.kilo/agent/django-htmx.md`: add the architecture rule — Wazely is a
   server-rendered HTMX SPA; new dashboard features render partials for
   `HX-Request` via `SPAContentMixin`; no full-page navigation for in-app
   links; no React/Vue/Angular unless explicitly requested.
4. `.kilo/agent/ui.md`: SPA UX states line (loading bar, toasts, empty/error
   states across swaps).
5. `AGENTS.md`: add "Frontend architecture" paragraph under Development
   Principles stating the same rule.

## Step 8 — Tests

Existing tests keep passing unchanged (they don't send `HX-Request`).
Add to `apps/dashboard/tests.py` (or a new `apps/core/tests.py` for the
middleware/mixin — recommended):

- `SPAContentMixin`: `RequestFactory` GET with `HX-Request: true` renders
  `<app>/_content.html`; without the header renders `shell.html`.
- Middleware: anonymous HTMX GET on a protected route returns `204` with
  `HX-Redirect` pointing at login (with `next`); anonymous non-HTMX GET still
  302-redirects; logged-in HTMX GET unaffected.
- OOB toasts: response with messages contains
  `hx-swap-oob="beforeend:#toast-container"`.
- Per-route: HTMX GET returns 200, uses the `_content.html` partial, and does
  not contain `<!DOCTYPE html>` or `main-shell` (no shell markup).
- Gallery: HX variant renders partial.

## Step 9 — Validation

```powershell
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --minify
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Live probe (runserver): full-page GET on all 9 routes → 200 with shell; same
routes with `HX-Request: true` → partials without shell markup; anonymous
HTMX GET → `204` + `HX-Redirect`; auth pages unchanged.

Manual browser pass: navigate all sidebar items with devtools network tab open
— no full document reloads; URL updates; back/forward restores content and
title; active nav follows; mobile drawer closes on nav; loading bar appears on
throttled network; keyboard focus moves to the new heading; theme and sidebar
collapse persist; logout toast + redirect work.

## Preserve — do not break

- All contracts listed in `htmx-patterns` and `wazely-ui` skills.
- `HTMXAccountMixin`, adapter, allauth URL names, `#auth-form` swap target,
  login field named `login`, `#toast-container` id, `data-theme`/`wazely-theme`
  and `data-sidebar`/`wazely-sidebar` keys.
- The 29 existing tests (only additive changes allowed to them).

## Risks

- **htmx history interplay** — `hx-history-elt` + `hx-push-url` must restore
  cached main content on back/forward; verify early on one route before
  converting all.
- **Title duplication** — title string lives in `index.html` block and
  `_content.html` `data-page-title`; documented in skills, keep adjacent.
- **OOB toast + reduced-motion timer** — dynamically inserted toasts need the
  afterSwap timer hook (Step 5.6) or they persist until manually closed.
- **Login-redirect middleware false positives** — scope strictly to redirects
  targeting the login URL; test the logged-out HTMX and non-HTMX paths.

## Out of scope

Real features behind placeholder routes, skeleton loading states, scroll
restoration beyond `show:window:top`, auth-page-to-auth-page SPA transitions,
self-hosted fonts, i18n, any backend logic beyond views/middleware/templates.
