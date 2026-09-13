---
name: htmx-patterns
description: HTMX patterns for Django including partial templates, hx-* attributes, and dynamic UI without JavaScript. Use when building interactive UI, handling AJAX requests, creating dynamic components, or doing SPA/single page application navigation, history, active nav, page titles, OOB swaps, or login-redirect handling in the Wazely shell.
---

# HTMX Patterns for Django

## Core Philosophy

- Server renders HTML, not JSON - HTMX requests return HTML fragments, not data
- Partial templates for dynamic updates - separate `_partial.html` files for HTMX responses
- Progressive enhancement - pages work without JavaScript, HTMX enhances UX
- Minimal client-side complexity - let the server do the heavy lifting

## Critical Hints & Reminders

### UX Best Practices

**Always include loading indicators**
- Use `hx-indicator` to show loading states during requests
- Users should never wonder if their action worked
- Example: `<button hx-get="/data/" hx-indicator="#spinner">Load</button>`

**Always provide user feedback**
- Use Django messages framework for success/error feedback
- Return error messages in HTMX responses, not silent failures
- Show what happened after an action completes

**Handle errors gracefully**
- Return proper HTTP status codes (400 for validation errors, 500 for server errors)
- Render form errors in partial templates
- Don't swallow exceptions - log and show user-friendly messages

### Django-Specific Patterns

**Always detect HTMX requests**
- Check `request.headers.get("HX-Request")` to detect HTMX requests
- Return partial templates for HTMX, full page templates otherwise
- Pattern: `if request.headers.get("HX-Request"): return render(request, "_partial.html", context)`

**Always return partials for HTMX**
- HTMX requests should return `_partial.html` templates, not full pages with `base.html`
- Full page responses to HTMX requests break the UX and send duplicate HTML
- Partials should be self-contained HTML fragments

**Always validate request.method**
- Check `request.method == "POST"` before processing form data
- Return proper status codes (405 Method Not Allowed for wrong methods)

**CSRF is already configured globally**
- The base template has `hx-headers` on `<body>` - no need to add CSRF tokens to individual forms
- All HTMX requests automatically include the CSRF token

### Template Organization

**Naming convention**
- Partials: `_partial.html` (underscore prefix)
- Full pages: `page.html` (no prefix)
- Example: `posts/list.html` (full page) includes `posts/_list.html` (partial)

**Structure**
- Full page template extends `base.html` and includes partial
- Partial contains only the dynamic HTML fragment
- HTMX targets the partial's container div

**Keep partials focused**
- Each partial should represent one logical UI component
- Avoid partials that are too large or do too much
- Compose larger UIs from multiple smaller partials

## Django View Patterns

### HTMX Detection

Check the `HX-Request` header to detect HTMX requests:

```python
def my_view(request):
    context = {...}

    if request.headers.get("HX-Request"):
        return render(request, "app/_partial.html", context)

    return render(request, "app/full_page.html", context)
```

### Form Handling Pattern

Key points:
- Validate form normally
- On success: return partial with new data OR trigger client-side event
- On error: return partial with form errors
- Always handle both HTMX and non-HTMX cases

```python
def create_view(request):
    if request.method == "POST":
        form = MyForm(request.POST)
        if form.is_valid():
            obj = form.save()
            if request.headers.get("HX-Request"):
                return render(request, "app/_item.html", {"item": obj})
            return redirect("app:list")

        # Return form with errors
        if request.headers.get("HX-Request"):
            return render(request, "app/_form.html", {"form": form})
    else:
        form = MyForm()

    return render(request, "app/create.html", {"form": form})
```

## SPA Shell Pattern

Wazely's authenticated area is a server-rendered HTMX SPA: `shell.html`
(sidebar, navbar, `#main-content`, `#toast-container`) renders once per full
page load; in-app navigation swaps only `#main-content`. Django keeps
rendering everything — there is no client-side framework and no `hx-boost`.

### The contract

- **Views**: dashboard pages use `SPAContentMixin` from `apps.core.mixins`,
  first in the MRO. It renders the app's content partial for
  `HX-Request: true` and the full page otherwise. The partial is derived from
  `template_name` (`<app>/index.html` → `<app>/_content.html`,
  `<app>/<page>.html` → `<app>/_<page>_content.html`); set
  `partial_template_name` to override.

  ```python
  class IndexView(SPAContentMixin, LoginRequiredMixin, TemplateView):
      template_name = "conversations/index.html"
  ```

- **Templates**: the page template extends `shell.html` and includes the
  content partial. The partial's root element carries
  `data-page-title="… · Wazely"` — kept identical to `{% block title %}` in
  the page template (the two strings are duplicated; keep them adjacent) —
  then `components/_page_header.html`, the page body, and finally
  `partials/_toasts_oob.html`. Never put page-level markup in `shell.html`:
  blocks do not propagate through includes, so anything that must swap with
  the page belongs in the content partial.
- **Nav links** keep their `href` (progressive enhancement, middle-click,
  copy-link) and add the SPA attributes; the mobile drawer closes on click:

  ```html
  <a href="{{ url }}" hx-get="{{ url }}" hx-target="#main-content"
     hx-swap="innerHTML show:window:top" hx-push-url="true"
     @click="$store.ui.drawerOpen = false">…</a>
  ```

  `<main id="main-content" hx-history-elt>` marks the history cache element,
  so back/forward restore the cached content and title.
- **Toasts over HTMX**: content partials end with
  `{% include "partials/_toasts_oob.html" %}`, which renders Django messages
  with `hx-swap-oob="beforeend:#toast-container"` on each toast root — htmx
  appends them to the persistent container instead of swapping them into
  `#main-content`. It no-ops on full page renders; `partials/_messages.html`
  owns those.
- **Login redirects**: `apps.core.middleware.HTMXLoginRedirectMiddleware`
  converts redirects *to the login URL* into `204 + HX-Redirect` (preserving
  `?next=`) for `HX-Request` requests, so an expired session mid-navigation
  triggers a full-page redirect instead of a broken partial. All other
  redirects pass through untouched.
- **Client sync** (all in `app.js`, hooked on `htmx:afterSwap`, which also
  fires on history restores and after the URL was pushed): move
  `aria-current="page"` to the sidebar link matching `location.pathname`, set
  `document.title` from `data-page-title`, focus the new `h1[tabindex="-1"]`,
  and arm reduced-motion auto-dismiss timers for newly inserted toasts. Sync
  runs only for *page-content swaps* — a swap whose root carries
  `data-page-title` — so swapping a form with validation errors never steals
  focus or rewrites the title. A delayed (~200ms) global progress bar shows
  for slow requests, and `htmx:responseError` appends an error toast (HTTP
  errors only; transport failures fire `htmx:sendError`/`htmx:timeout`).

### Auth shell (second SPA surface)

The auth area is its own SPA surface: `account/base.html` keeps the brand
panel and form column, and `#auth-content` (with `hx-history-elt`) is the
swap target. `HTMXAccountMixin` (`apps/accounts/views.py`) mirrors
`SPAContentMixin`:

- **POST** renders `htmx_template` (the form partial) → htmx swaps
  `#auth-form`.
- **GET** renders `htmx_content_template` (the page content partial) → htmx
  swaps `#auth-content`; auth links use the same
  `hx-get`/`hx-target`/`hx-swap`/`hx-push-url` attributes as dashboard links.
- **Redirects** become `HX-Redirect` (full page load) — except when
  `htmx_redirect_in_shell` is set and the target resolves to an
  `AUTH_SHELL_URL_NAMES` page, which becomes
  `HX-Location: {"path": …, "target": "#auth-content", "swap": "innerHTML"}`.
  htmx applies that client-side and pushes history, so signup → verify-email
  and reset → check-email stay in the shell. Login success always leaves the
  shell (`HX-Redirect` to the dashboard).

Auth forms share `account/_auth_form.html` + `account/_auth_submit.html`.
Auth pages reached by full page load from an email link (reset from key,
confirm email) render normally; their in-app links still swap.

### When NOT to use HTMX navigation

- Crossing between top-level shells (login success → dashboard, logout) is a
  full page load via `HX-Redirect`.
- External links and downloads stay plain links.
- Pages whose failure path re-renders a whole document (email confirmation)
  keep a plain form submission.
- New dashboard features join the SPA pattern — render the partial for
  `HX-Request` via `SPAContentMixin`; no full-page navigation for in-app
  links.

## Response Headers Reference

HTMX respects special response headers for client-side behavior:

### HX-Trigger
Trigger client-side events after response
- Use case: Update other parts of page after action
- Example: `response["HX-Trigger"] = "itemCreated"`
- Template listens: `<div hx-get="/count/" hx-trigger="itemCreated from:body">`

### HX-Redirect
Client-side redirect
- Use case: Redirect after successful action
- Example: `response["HX-Redirect"] = reverse("app:detail", args=[obj.pk])`

### HX-Retarget / HX-Reswap
Override hx-target and hx-swap from server
- Use case: Different targets for success vs error
- Success: `response["HX-Retarget"] = "#main"`
- Error: Return partial without changing target (targets the form)

### HX-Refresh
Force full page refresh
- Use case: Major state change that affects whole page
- Example: `response["HX-Refresh"] = "true"`

## Common Pitfalls

- **Missing loading indicators**: Always use `hx-indicator` - users click multiple times without feedback
- **Full pages in HTMX responses**: Return `_partial.html`, not full pages with `base.html` - check `HX-Request` header
- **Not handling form errors**: Always return the form with errors on validation failure, not just the success case
- **Not disabling buttons**: Use `hx-disabled-elt="this"` to prevent duplicate submissions
- **N+1 queries**: HTMX views need `select_related()`/`prefetch_related()` just like regular views

## Integration with Other Skills

- **django-templates**: Partial template organization and inheritance patterns
- **django-forms**: HTMX form submission and validation
- **django-extensions**: Use `show_urls` to verify HTMX endpoints
- **pytest-django-patterns**: Testing HTMX endpoints and headers
- **systematic-debugging**: Debug HTMX request/response issues
