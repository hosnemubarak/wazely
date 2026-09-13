# Wazely — Agent Notes

## Purpose

Wazely will become an AI-powered WhatsApp customer communication platform: a place where
organizations manage WhatsApp conversations with their customers, assisted by AI agents and a
knowledge base.

## Current Stage

Foundation plus authentication and the UI shell. The repository holds a Django +
PostgreSQL project with django-allauth (email login, password reset, email
verification), the Tailwind design system, the app shell (sidebar/navbar), and
placeholder routes per app (overview, conversations, contacts, WhatsApp accounts,
agents, knowledge base, team, settings) backed by empty states.

There are no models beyond the custom user, no forms/serializers/services, and no
WhatsApp, OpenAI, RAG, or agent integrations yet.

## Current Technology Stack

- Python 3.12+
- Django (`config` project package)
- PostgreSQL through `psycopg`
- `python-dotenv` for environment configuration
- Tailwind CSS v4 (standalone binary; see "Frontend build" below)
- HTMX 2.0.6 and Alpine.js 3.15.0, vendored under `static/js/` (no npm)

Not part of the project yet: REST framework, Celery, Redis, Docker, and any AI
or messaging SDK.

## Frontend build

Tailwind CSS is built with the standalone binary (no Node, no package.json):

1. Download once per machine into `bin/` (git-ignored):
   `https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe`
2. Build commands (from the repo root):

```powershell
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --watch   # dev
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --minify  # before commit
```

The built `static/css/app.css` is committed — rebuild it whenever template
classes change, and commit the rebuilt file. There is no CI/deploy build step;
`collectstatic` picks up the committed file. See `.kilo/skill/wazely-ui/SKILL.md`
for the design system itself.

## App Layout

All apps live under `apps/` and are registered in `INSTALLED_APPS` as `apps.<name>`:

`accounts`, `organizations`, `whatsapp`, `conversations`, `contacts`, `agents`, `knowledge`,
`ai`, `dashboard`.

Each one is intentionally empty and reserves a bounded context for future work.

## Development Principles

- Keep configuration in environment variables; never hardcode secrets or credentials.
- Keep `config/settings.py` limited to standard Django configuration.
- Keep each app inside its own domain boundary; no cross-app shortcuts.
- Prefer small, verifiable changes; `python manage.py check` must stay clean.
- Add dependencies only when a requested feature needs them.

### Frontend architecture

The authenticated area is a server-rendered HTMX SPA: the shell (sidebar,
navbar, `#toast-container`) renders once and only `#main-content` swaps.
Dashboard views use `SPAContentMixin` from `apps.core` to serve their content
partial (`<app>/_content.html`) for `HX-Request` and the full page otherwise;
in-app links keep their `href` and add `hx-get` + `hx-target="#main-content"`
+ `hx-swap="innerHTML show:window:top"` + `hx-push-url="true"` (no
`hx-boost`). Login redirects for HTMX requests are converted to
`204 + HX-Redirect` by `apps.core.middleware.HTMXLoginRedirectMiddleware`.
No React/Vue/Angular or any client-side SPA framework. Auth pages keep full
navigation between pages; only their form submissions are HTMX. See the
`htmx-patterns` skill ("SPA shell pattern") for the full contract.

## Working Agreement

**Do not implement features unless explicitly requested.** When asked for work, stay within
the requested scope and do not add speculative code, abstractions, models, endpoints, or
frontend assets.

## Kilo Agents and Skills

Shared, version-controlled and committed with the project. See `.kilo/README.md` for the
full list and usage examples.

- `.kilo/agent/*.md` — roles you can pick per task: `django-htmx`, `ui`, `data`,
  plus subagents `code-reviewer` and `github-workflow` that other agents invoke.
- `.kilo/skill/<name>/SKILL.md` — knowledge shared across roles, like
  `django-models`, `htmx-patterns`, `celery-patterns`, `code-quality`.

Rule of thumb: this file holds rules that always apply, an agent file holds how one role
behaves, and a skill holds knowledge two or more roles need. If only one role needs it,
keep it in that agent file rather than creating a skill.

Personal settings (model, theme, API keys) belong in `~/.config/kilo/`, never in this repo.

