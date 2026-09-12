# Wazely — Agent Notes

## Purpose

Wazely will become an AI-powered WhatsApp customer communication platform: a place where
organizations manage WhatsApp conversations with their customers, assisted by AI agents and a
knowledge base.

## Current Stage

Foundation only. The repository holds a clean Django + PostgreSQL project with empty apps.

There are no models, views, URLs (beyond `admin/`), templates, forms, serializers, services,
repositories, or integrations. Nothing about WhatsApp, OpenAI, RAG, or agents is implemented.

## Current Technology Stack

- Python 3.12+
- Django (`config` project package)
- PostgreSQL through `psycopg`
- `python-dotenv` for environment configuration

Not part of the project yet: HTMX, JavaScript, CSS, REST framework, Celery, Redis, Docker,
and any AI or messaging SDK.

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

## Working Agreement

**Do not implement features unless explicitly requested.** When asked for work, stay within
the requested scope and do not add speculative code, abstractions, models, endpoints, or
frontend assets.

## Kilo Agents and Skills

Shared, version-controlled and committed with the project. See `.kilo/README.md` for the
full list and usage examples.

- `.kilo/agent/*.md` — roles you can pick per task: `django`, `htmx`, `ui`, `data`,
  plus subagents `code-reviewer` and `github-workflow` that other agents invoke.
- `.kilo/skill/<name>/SKILL.md` — knowledge shared across roles, like
  `django-models`, `htmx-patterns`, `celery-patterns`, `code-quality`.

Rule of thumb: this file holds rules that always apply, an agent file holds how one role
behaves, and a skill holds knowledge two or more roles need. If only one role needs it,
keep it in that agent file rather than creating a skill.

Personal settings (model, theme, API keys) belong in `~/.config/kilo/`, never in this repo.

