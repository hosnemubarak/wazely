# Wazely

Wazely is the foundation for an AI-powered WhatsApp customer communication platform.

This repository currently contains **only** a clean Django + PostgreSQL project skeleton with
empty apps. No application functionality has been implemented yet.

## Current Stack

- Python 3.12+
- Django
- PostgreSQL (via `psycopg`)
- `python-dotenv` for environment configuration

No frontend stack, REST API, task queue, or AI integration is present at this stage.

## Project Structure

```text
wazely/
├── manage.py
├── README.md
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── __init__.py
│   ├── accounts/
│   ├── organizations/
│   ├── whatsapp/
│   ├── conversations/
│   ├── contacts/
│   ├── agents/
│   ├── knowledge/
│   ├── ai/
│   └── dashboard/
│
└── agent/
    └── agent.md
```

Every app under `apps/` contains only the standard empty Django files
(`__init__.py`, `admin.py`, `apps.py`, `models.py`, `tests.py`, `migrations/__init__.py`).

## Local PostgreSQL Setup

1. Install PostgreSQL and make sure the server is running locally.
2. Create the database used by the project:

   ```bash
   psql -U postgres -c "CREATE DATABASE wazely;"
   ```

3. Note the credentials for the PostgreSQL user you intend to use; they are supplied to
   Django through environment variables (see below).

## Virtual Environment Setup

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Configuration

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TIME_ZONE=UTC

DB_NAME=wazely
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
```

`.env` is ignored by Git. Database credentials and the secret key are never hardcoded in
`config/settings.py`.

## Migrations

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

## Running the Development Server

```bash
python manage.py runserver
```

The site is then available at http://127.0.0.1:8000/ and the Django admin at
http://127.0.0.1:8000/admin/ (create a superuser first with
`python manage.py createsuperuser`).
