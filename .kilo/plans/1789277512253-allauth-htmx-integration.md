# django-allauth + HTMX Integration Plan

Integrate `django-allauth` into Wazely for email/password registration, login, email
verification, and password resets — session-based, HTMX-compatible, no JS frameworks.

## Resolved decisions

| Decision | Choice |
|---|---|
| User model | Custom email-based `User` in `apps.accounts` (`USERNAME_FIELD = "email"`) |
| HTMX delivery | Vendored `htmx.min.js` in `static/js/` (no CDN) |
| Post-login landing | Minimal login-protected `HomeView` in `apps.dashboard` |
| Verification policy | Mandatory (`ACCOUNT_EMAIL_VERIFICATION = "mandatory"`) |
| Auth backend | `allauth.account.auth_backends.AuthenticationBackend` alone (subclasses `ModelBackend`, admin login keeps working) |
| Social providers | Out of scope — only `allauth` + `allauth.account`, no `allauth.socialaccount` |

## Conventions this plan follows

- Apps live under `apps/`, registered as `apps.<name>`; auth code stays inside `apps.accounts`.
- Templates: full pages extend a project-root `templates/base.html`; HTMX partials are
  `_underscore.html` fragments (`.kilo/skill/django-templates`, `.kilo/skill/htmx-patterns`).
- HTMX detection via `request.headers.get("HX-Request")`; partials returned for HTMX requests;
  CSRF via `hx-headers` on `<body>` plus `{% csrf_token %}` in every form (progressive
  enhancement — forms carry `method="post"` + `action` so they work without JS).
- All auth/business logic in the backend (allauth views + thin subclasses); templates only
  render — no logic beyond loops/conditionals/URL tags.
- Settings read from env; nothing hardcoded. `python manage.py check` must stay clean.

## Prerequisites

- PostgreSQL running and reachable (`DB_*` in `.env`).
- Use the project venv: `.venv\Scripts\python.exe manage.py ...` (PowerShell).
- **Database reset warning**: `AUTH_USER_MODEL` changes require a fresh DB. If `migrate` was
  ever run against the dev DB, drop and recreate it first (`DROP DATABASE wazely;` +
  `CREATE DATABASE wazely;` in psql, or via pgAdmin). No real data exists yet, so this is safe.
- Pin allauth **>= 65.4** (new-style settings `ACCOUNT_LOGIN_METHODS` / `ACCOUNT_SIGNUP_FIELDS`
  require it). Repo style keeps `requirements.txt` loose, but record the installed version.

---

## Step 1 — Dependency

`requirements.txt`:

```
Django
psycopg[binary]
python-dotenv
django-allauth>=65.4
```

Install:

```powershell
.venv\Scripts\pip.exe install django-allauth
.venv\Scripts\pip.exe freeze | Select-String allauth   # note installed version
```

## Step 2 — Custom user model (`apps.accounts`)

`apps/accounts/models.py` (terse style, no comments — match existing app code):

```python
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email
```

`apps/accounts/admin.py`:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
```

## Step 3 — `config/settings.py` changes

Modify these existing sections (keep the file's documented style):

```python
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",          # required by allauth
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS: list[str] = [
    "allauth",
    "allauth.account",
]

MIDDLEWARE = [
    # ... existing entries unchanged ...
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",   # required by allauth
]
```

In `TEMPLATES[0]`: `"DIRS": [BASE_DIR / "templates"],`

Near the auth-related settings add:

```python
AUTH_USER_MODEL = "apps.accounts.User"
```

(Note: `AUTH_USER_MODEL` uses the app label `accounts`, matching `name = "apps.accounts"`
— verify with `python manage.py check`; if the label differs use what check reports.)

After the static files section add:

```python
STATICFILES_DIRS = [BASE_DIR / "static"]
```

At the bottom, add two documented sections (match file comment style):

```python
# Email
# Console backend for local development; SMTP settings come from the environment.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = os.getenv("EMAIL_PORT", "587")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")

# django-allauth
# https://docs.allauth.org/en/latest/account/configuration.html
AUTHENTICATION_BACKENDS = [
    "allauth.account.auth_backends.AuthenticationBackend",
]
SITE_ID = 1
LOGIN_REDIRECT_URL = "dashboard:home"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv("ACCOUNT_DEFAULT_HTTP_PROTOCOL", "http")
```

Defaults kept on purpose (note in review, no config needed): login attempt limit (5 tries /
30 min lockout) and allauth rate limiting are on by default.

## Step 4 — `.env.example` additions

```
# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
#EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#EMAIL_HOST=smtp.example.com
#EMAIL_PORT=587
#EMAIL_HOST_USER=
#EMAIL_HOST_PASSWORD=
#EMAIL_USE_TLS=True
#DEFAULT_FROM_EMAIL=Wazely <no-reply@example.com>

# django-allauth
ACCOUNT_DEFAULT_HTTP_PROTOCOL=http
```

## Step 5 — Migrations

```powershell
.venv\Scripts\python.exe manage.py makemigrations accounts
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run   # must report no changes
.venv\Scripts\python.exe manage.py check                             # must be clean
```

This creates `apps/accounts/migrations/0001_initial.py` plus allauth/sites tables.
Optional: tidy the `django_site` row (name/domain) via admin — not blocking, links are
built from the request host in normal flows.

## Step 6 — Project-level layout, static assets, base template

New files:

```
templates/base.html
templates/partials/_navbar.html
templates/partials/_messages.html
templates/partials/_form_fields.html
static/js/htmx.min.js        (vendored)
static/css/base.css          (minimal)
```

Vendor HTMX (pin an exact 2.x version, e.g. 2.0.6 or latest at implementation time):

```powershell
New-Item -ItemType Directory -Force static\js, static\css | Out-Null
Invoke-WebRequest -Uri "https://unpkg.com/htmx.org@2.0.6/dist/htmx.min.js" -OutFile static\js\htmx.min.js
```

`templates/base.html`:

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Wazely{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% include "partials/_navbar.html" %}
    <main class="container">
        {% include "partials/_messages.html" %}
        {% block content %}{% endblock %}
    </main>
    <script src="{% static 'js/htmx.min.js' %}" defer></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

`templates/partials/_navbar.html`:

```html
<header class="navbar">
    <a class="brand" href="{% url 'dashboard:home' %}">Wazely</a>
    <nav>
        {% if request.user.is_authenticated %}
            <span class="navbar-user">{{ request.user.email }}</span>
            <form method="post" action="{% url 'account_logout' %}" hx-post="{% url 'account_logout' %}" class="inline-form">
                {% csrf_token %}
                <button type="submit">Log out</button>
            </form>
        {% else %}
            <a href="{% url 'account_login' %}">Log in</a>
            <a href="{% url 'account_signup' %}">Sign up</a>
        {% endif %}
    </nav>
</header>
```

`templates/partials/_messages.html`:

```html
{% if messages %}
    <ul class="messages">
        {% for message in messages %}
            <li class="message message-{{ message.tags }}">{{ message }}</li>
        {% endfor %}
    </ul>
{% endif %}
```

`templates/partials/_form_fields.html` (shared field renderer, keeps form partials DRY):

```html
{% if form.non_field_errors %}
    <ul class="form-errors">
        {% for error in form.non_field_errors %}<li>{{ error }}</li>{% endfor %}
    </ul>
{% endif %}
{% for field in form %}
    <div class="form-field{% if field.errors %} has-errors{% endif %}">
        <label for="{{ field.id_for_label }}">{{ field.label }}</label>
        {{ field }}
        {% for error in field.errors %}<p class="field-error">{{ error }}</p>{% endfor %}
    </div>
{% endfor %}
```

`static/css/base.css` — minimal (~60 lines): basic reset, `.container`, `.navbar`,
`.auth-card` (centered card), `.form-field`/`.field-error`/`.form-errors`, `.messages`,
plus the indicator rules (display-based so the "Working…" text is hidden without JS):

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
```

No CSS framework, no other JS. Presentation stays entirely in this stylesheet and templates.

## Step 7 — Backend logic for HTMX (`apps/accounts/views.py`)

Two responsibilities only: pick the partial template for HTMX requests, and convert
redirect responses to `HX-Redirect` (so HTMX performs a full-page navigation on success).
All authentication logic itself stays inside allauth.

```python
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
```

Why `dispatch`: a single interception point converts every success redirect —
`form_valid` returns, allauth's `perform_login` results, the logged-in-user redirect on
GET, and defensively any raised `ImmediateHttpResponse`. `get_template_names` covers both
the initial GET and the invalid-form re-render, so validation errors come back as the
form partial and HTMX swaps it inline.

## Step 8 — URLs

`apps/accounts/urls.py` — our own URLconf that **replaces** `allauth.urls`, keeping
allauth's namespace (`account`) and URL names so `{% url 'account_login' %}`,
`LOGIN_URL`-style reverses, and allauth's internal `reverse()` calls keep working:

```python
from allauth.account import views as account_views
from django.urls import path

from . import views

app_name = "account"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("password/reset/", views.PasswordResetView.as_view(), name="reset_password"),
    path("password/reset/done/", account_views.PasswordResetDoneView.as_view(), name="reset_password_done"),
    path("password/reset/key/<uidb36>-<keyhash>/", views.PasswordResetFromKeyView.as_view(), name="reset_password_from_key"),
    path("password/reset/key/done/", account_views.PasswordResetFromKeyDoneView.as_view(), name="reset_password_from_key_done"),
    path("verify-email/", account_views.EmailVerificationSentView.as_view(), name="email_verification_sent"),
    path("confirm-email/<key>/", account_views.ConfirmEmailView.as_view(), name="confirm_email"),
]
```

**Critical**: before writing this file, open the installed
`.venv\Lib\site-packages\allauth\urls.py` and copy each path pattern verbatim (the
reset-key route may be a `re_path` in some versions). Names must match exactly.
If any test hits a `NoReverseMatch`, an allauth-internal URL is missing — add it from
that same file.

`config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
]
```

## Step 9 — Dashboard landing placeholder

`apps/dashboard/views.py`:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"
```

`apps/dashboard/urls.py`:

```python
from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]
```

`apps/dashboard/templates/dashboard/home.html` — minimal placeholder, extends
`base.html`, shows the logged-in email and a note that the dashboard is coming. Its only
job is to be a real `@login_required` destination proving the session cycle end-to-end.

## Step 10 — allauth template overrides

Location: `apps/accounts/templates/account/` (allauth looks up `account/<name>.html`
across all template sources; keeping them inside the owning app respects app boundaries).

**First**: list `.venv\Lib\site-packages\allauth\account\templates\account\` and confirm
the exact template names for the installed version before creating overrides. Expected set:

```
account/base.html                        # one line: {% extends "base.html %}
account/login.html                       # full page, includes _login_form.html
account/_login_form.html                 # HTMX partial
account/signup.html                      # full page, includes _signup_form.html
account/_signup_form.html                # HTMX partial
account/logout.html                      # GET confirmation page with POST form
account/password_reset.html              # full page, includes _password_reset_form.html
account/_password_reset_form.html        # HTMX partial
account/password_reset_done.html         # full page ("check your email")
account/password_reset_from_key.html     # full page, includes _password_reset_from_key_form.html
account/_password_reset_from_key_form.html  # HTMX partial
account/password_reset_from_key_done.html   # full page ("password changed")
account/verification_sent.html           # full page (confirm the exact name in site-packages)
account/email_confirm.html               # email-confirmation interstitial (plain POST form)
account/account_inactive.html            # fallback for inactive-account response
```

`account/base.html` (makes allauth's own fallback pages inherit the project chrome):

```html
{% extends "base.html" %}
```

Full-page pattern (`account/login.html` — signup, password_reset, password_reset_from_key
follow the same shape, adjusting heading, partial, and footer links):

```html
{% extends "account/base.html" %}
{% block title %}Log in · Wazely{% endblock %}
{% block content %}
<div class="auth-card">
    <h1>Log in</h1>
    {% include "account/_login_form.html" %}
    <p class="auth-links">
        <a href="{% url 'account_signup' %}">Create an account</a> ·
        <a href="{% url 'account_reset_password' %}">Forgot password?</a>
    </p>
</div>
{% endblock %}
```

Partial pattern (`account/_login_form.html` — all four form partials follow this shape;
only the URL, button label, and wrapper heading text differ). The wrapper div is the swap
target and lives inside the partial so `hx-swap="outerHTML"` replaces it cleanly:

```html
<div id="auth-form">
    <form method="post" action="{% url 'account_login' %}"
          hx-post="{% url 'account_login' %}"
          hx-target="#auth-form" hx-swap="outerHTML"
          hx-indicator="#auth-submit-indicator"
          hx-disabled-elt="find button[type='submit']">
        {% csrf_token %}
        {% include "partials/_form_fields.html" %}
        <button type="submit">Log in</button>
        <span id="auth-submit-indicator" class="htmx-indicator">Working…</span>
    </form>
</div>
```

Partials for: `_signup_form.html` (`account_signup`), `_password_reset_form.html`
(`account_reset_password`), `_password_reset_from_key_form.html`
(`account_reset_password_from_key`).

Simple full pages (extend `account/base.html`, one heading + optional link): 
`logout.html` (POST form confirming logout), `password_reset_done.html`,
`password_reset_from_key_done.html`, `verification_sent.html`, `email_confirm.html`
(POST form with a "Confirm" button), `account_inactive.html`.

`password_reset_from_key.html` full page: heading "Choose a new password" + include of
its partial. Signup page footer links to login; login links to signup and reset (shown above).

**Separation of concerns check**: no view or template contains auth decisions — templates
render `{{ form }}` fields, errors, and URLs; views only choose template/response shape.

## Step 11 — Smoke tests (`apps/accounts/tests.py`)

Plain `django.test.TestCase` (no new test dependencies — pytest adoption is out of scope).
Django 4.2+ test client supports `headers=`:

```python
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
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/_login_form.html")
        self.assertNotContains(response, "<!DOCTYPE html>")

    def test_htmx_valid_login_returns_hx_redirect(self):
        response = self.client.post(
            reverse("account_login"),
            {"login": "user@example.com", "password": "correct-horse-battery"},
            headers={"HX-Request": "true"},
        )
        self.assertEqual(response.headers.get("HX-Redirect"), reverse("dashboard:home"))


class DashboardAccessTests(TestCase):
    def test_anonymous_home_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('dashboard:home')}")


class PasswordResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("user@example.com", "correct-horse-battery")
        EmailAddress.objects.create(user=cls.user, email=cls.user.email, primary=True, verified=True)

    def test_reset_request_sends_email(self):
        response = self.client.post(reverse("account_reset_password"), {"email": "user@example.com"})
        self.assertRedirects(response, reverse("account_reset_password_done"))
        self.assertEqual(len(mail.outbox), 1)
```

Notes:
- allauth's login form field is named `login` (it maps to the email here).
- If rate limiting trips during the test run (failed-login attempts), wrap the affected
  test class with `@override_settings` disabling `ACCOUNT_RATE_LIMITS` per the installed
  version's docs.
- Email confirmation-by-key test: extract the confirmation key from
  `mail.outbox[0].body` URL or `EmailAddress ... get_email_confirmation_model()`; follow
  the confirm flow and assert `verified=True` and subsequent login succeeds.

## Step 12 — Validation checklist

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test apps.accounts apps.dashboard
.venv\Scripts\python.exe manage.py runserver
```

Manual flow in the browser (email lands in the runserver console with the console backend):

1. `/accounts/signup/` → register → redirected to "verification sent" page; console shows email.
2. Open the confirmation link from the console email → confirm → log in → land on `/` (dashboard home)
   showing the email + logout.
3. Log out via navbar (HTMX POST → full navigation back to login).
4. Password reset: request → console email → open link → set new password → log in with it.
5. HTMX behavior: on login page, submit an empty/wrong form → inline errors appear inside the
   card **without a full page reload** (Network tab shows the `HX-Request` header and an
   HTML fragment response); submit valid credentials → full page navigation to dashboard.
6. While logged out, visit `/` → redirected to login with `?next=/`.
7. `createsuperuser` with email works; `/admin/` login works.

---

## File inventory

**Modified**: `requirements.txt`, `config/settings.py`, `config/urls.py`, `.env.example`,
`apps/accounts/models.py`, `apps/accounts/admin.py`, `apps/accounts/tests.py`.

**New backend**: `apps/accounts/views.py`, `apps/accounts/urls.py`,
`apps/accounts/migrations/0001_initial.py`, `apps/dashboard/views.py`,
`apps/dashboard/urls.py`.

**New templates**: `templates/base.html`, `templates/partials/_navbar.html`,
`templates/partials/_messages.html`, `templates/partials/_form_fields.html`,
`apps/accounts/templates/account/` (base, login, _login_form, signup, _signup_form,
logout, password_reset, _password_reset_form, password_reset_done,
password_reset_from_key, _password_reset_from_key_form, password_reset_from_key_done,
verification_sent, email_confirm, account_inactive),
`apps/dashboard/templates/dashboard/home.html`.

**New static**: `static/js/htmx.min.js` (vendored), `static/css/base.css` (minimal).

## Risks & edge cases

- **DB reset** if previously migrated (Step 0/prerequisites) — the only destructive step.
- **allauth version drift**: URL patterns, template names, and settings names verified
  against the installed version, not memory (Steps 7–10 call this out where it matters).
- **ImmediateHttpResponse edge paths** (e.g., inactive account) render full pages; the
  mixin's `try/except` catches and passes them through. Acceptable: our users are active
  (verification is handled via allauth's EmailAddress, not `is_active`).
- **CSRF-expired HTMX POST** returns Django's 403 page into the swap target — rare,
  acceptable at this stage; note for future hardening if it appears.
- **Rate limits** are on by default (5 failed logins / 30 min lockout, plus request rate
  limits) — a feature here, but keep test suites small or override in tests.

## Out of scope (explicit)

Social account providers, custom email copy/branding, remember-me, MFA, session
management views, password-change flows, pytest infrastructure, organizations linkage,
and any styling beyond the minimal stylesheet.
