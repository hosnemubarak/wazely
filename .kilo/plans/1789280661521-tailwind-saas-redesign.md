# Wazely UI Redesign — Tailwind SaaS Design System

Full-interface redesign: replace the hand-written Green Deck CSS with a Tailwind v4
design system (emerald identity, Inter type), rebuild the auth pages and dashboard
shell as a cohesive B2B SaaS product, and document the new system in `.kilo`.

Backend behavior is preserved. No model changes.

## Resolved decisions

| Decision | Choice |
|---|---|
| Tailwind delivery | Standalone `tailwindcss.exe` v4 binary — no Node, no package.json. Built CSS committed |
| Brand color | Emerald ramp, primary `#059669` (600), hover `#047857` (700); slate neutrals |
| Default theme | Light-first, dark fully supported, OS-aware on first visit, choice persisted |
| Interactions | Alpine.js 3 (vendored, not CDN) + existing HTMX |
| Nav destinations | Real placeholder route per owning app (8 routes) |
| Typeface | Inter (Google Fonts, variable) + JetBrains Mono for code/IDs |
| Auth layout | Split: form column + restrained emerald brand panel; single column ≤ lg |
| Components | Full inventory in `templates/components/` + DEBUG-only gallery at `/ui/` |
| Design docs | Delete `green-deck` skill, add `wazely-ui` skill, update agent rules |

## Preserve — do not break

These have passing tests or known-fragile behavior:

- `apps/accounts/adapter.py` (`is_ajax → False`) and `ACCOUNT_ADAPTER` — without it real
  browsers get JSON instead of HTML partials.
- `HTMXAccountMixin` in `apps/accounts/views.py`: partial template names, `HX-Redirect`
  conversion, `ImmediateHttpResponse` handling.
- allauth URL names in `apps/accounts/urls.py` (global, no `app_name`).
- Template names asserted by tests: `account/signup.html`, `account/_login_form.html`.
- Contracts: `#auth-form` swap target, `hx-post`/`hx-target`/`hx-swap="outerHTML"`,
  `hx-indicator`, `hx-disabled-elt`, `hx-headers` CSRF on `<body>`, `#toast-container` id,
  Django messages → toasts, `data-theme` attribute + `wazely-theme` localStorage key.
- Login form field is named `login`, not `email`.

---

## Step 1 — Tailwind toolchain

1. Create `bin/` and download the v4 standalone binary (Windows x64) from
   `tailwindlabs/tailwindcss` releases as `bin/tailwindcss.exe`.
2. Add to `.gitignore`: `bin/` (binary is machine-specific; the built CSS is committed).
3. Source file `static/css/app.src.css`; build output `static/css/app.css` (committed).
4. Build commands (PowerShell, run from repo root):

```powershell
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --watch   # dev
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --minify  # before commit
```

5. Document both commands in `AGENTS.md` (new short "Frontend build" section) and in the
   new skill. No CI/deploy step is added — `collectstatic` picks up the committed file.

## Step 2 — Design tokens (`static/css/app.src.css`)

```css
@import "tailwindcss";
@source "../../templates";
@source "../../apps";

@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

@theme {
  --color-brand-50:  #ecfdf5;  --color-brand-100: #d1fae5;
  --color-brand-200: #a7f3d0;  --color-brand-300: #6ee7b7;
  --color-brand-400: #34d399;  --color-brand-500: #10b981;
  --color-brand-600: #059669;  --color-brand-700: #047857;
  --color-brand-800: #065f46;  --color-brand-900: #064e3b;
  --color-brand-950: #022c22;
  --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
}
```

- Neutrals: Tailwind's built-in `slate`. Semantic: brand-600 (success), `amber-500`
  (warning), `red-600` (error), `sky-600` (info).
- Radius: `rounded-md` (6px) controls, `rounded-lg` (8px) cards/panels, `rounded-full`
  avatars/badges only. No oversized radii.
- Elevation: borders first (`border-slate-200` / `dark:border-white/10`), `shadow-xs`
  on cards, `shadow-lg` only for popovers/modals/toasts. No gradients except the auth
  brand panel.
- Type scale: auth headline `text-3xl font-semibold tracking-tight`; page title
  `text-2xl font-semibold tracking-tight`; section `text-lg font-semibold`; card title
  `text-sm font-semibold`; body `text-sm`; secondary `text-sm text-slate-500`; label
  `text-xs font-medium` (sentence case — drop the old uppercase-tracking buttons/labels);
  nav `text-sm font-medium`; button `text-sm font-medium`; meta `text-xs`.
- Component classes: use `@apply` in `app.src.css` for the highest-churn primitives only
  (`.btn`, `.btn-primary|secondary|ghost|danger`, `.input`, `.card`, `.badge-*`,
  `.nav-item`) so 20+ templates don't duplicate class soup. Everything else is utilities.
- Delete `static/css/base.css` once pages are migrated.

## Step 3 — Vendored JS

- `static/js/alpine.min.js` (Alpine 3.x, pinned version recorded in the skill), loaded
  `defer` **after** `app.js`.
- `static/js/app.js`: theme store, sidebar collapse/drawer store (both persisted to
  localStorage), toast dismissal, and:

```js
document.body.addEventListener("htmx:afterSwap", function (e) {
    if (window.Alpine) window.Alpine.initTree(e.target);
});
```

  (Required — swapped auth form partials contain Alpine components.)
- Keep `static/js/htmx.min.js` as is.

## Step 4 — Layout shell

- `templates/base.html` — html with `data-theme="light"` default, head theme script
  (localStorage → `prefers-color-scheme` → light), Inter/JetBrains Mono link,
  `app.css`, skip-to-content link, `#toast-container`, script tags. Blocks: `title`,
  `body`, `extra_css`, `extra_js`.
- `templates/shell.html` — authenticated app shell extending `base.html`: sidebar +
  navbar + `<main>`. Blocks: `page_title`, `breadcrumb`, `page_actions`, `content`.
- `templates/partials/_sidebar.html` — groups exactly as specified: **Overview**;
  **Workspace** (Conversations, Contacts, WhatsApp Accounts); **AI** (Agents, Knowledge
  Base); **Management** (Team, Settings). `w-64` expanded / `w-16` collapsed, smooth
  width transition, Lucide-style inline icons, `aria-current="page"` + brand-tinted
  active state, tooltips when collapsed, user block + logout at the bottom.
  Below `lg`: off-canvas drawer with overlay, `Esc` to close, body scroll lock.
- `templates/partials/_navbar.html` — sidebar toggle, page title/breadcrumb from blocks,
  search input (visibly disabled with a "Coming soon" tooltip — no fake search),
  notifications dropdown rendering an empty state (no fake counts), theme toggle, user
  menu (email, Settings link, Log out). No workspace switcher — no org models exist yet.

## Step 5 — Component library (`templates/components/`)

`_button.html`, `_input.html` (label, help text, error state, password visibility toggle),
`_card.html`, `_badge.html`, `_table.html`, `_empty_state.html`, `_dropdown.html`,
`_modal.html` (native `<dialog>` driven by Alpine — free focus trap and `Esc`),
`_alert.html`, `_toast.html`, `_spinner.html`, `_tooltip.html`, `_icon.html`
(name → inline SVG map, no icon dependency).

Gallery: `ComponentGalleryView` in `apps/dashboard/views.py`, template
`dashboard/ui_gallery.html`, registered in `config/urls.py` **only** under
`if settings.DEBUG`. It is the manual QA surface for every component in both themes.

## Step 6 — Auth pages

Rebuild `templates/account/base.html` as the split shell: form column (`max-w-sm`,
vertically centered, brand lockup, heading, subcopy, form, footer links) plus brand panel
(`hidden lg:flex`, emerald-900 surface, product name, one-line value proposition, 2–3
short proof points, no imagery). Single column with compact brand header below `lg`.

Rebuild all pages on it: `login`, `signup`, `password_reset`,
`password_reset_from_key` (confirmation), `password_reset_from_key_done` (complete),
`password_reset_done`, `verification_sent`, `email_confirm`, `logout`,
`account_inactive`.

Form partials (`_login_form.html`, `_signup_form.html`, `_password_reset_form.html`,
`_password_reset_from_key_form.html`) keep their filenames and HTMX attributes; restyle
only. `templates/partials/_form_fields.html` gains: floating/standard labels, per-field
error styling, `aria-invalid`/`aria-describedby`, and a password visibility toggle
branching on `field.field.widget.input_type == "password"`. Submit buttons show a spinner
via `hx-indicator` and disable via `hx-disabled-elt`.

## Step 7 — Placeholder routes

Each is `LoginRequiredMixin` + `TemplateView` extending `shell.html` with an
`_empty_state.html` body. ~10 lines per app; no models, no fake data.

| Nav item | App | URL | URL name |
|---|---|---|---|
| Overview | `dashboard` | `/` | `dashboard:home` |
| Conversations | `conversations` | `/conversations/` | `conversations:index` |
| Contacts | `contacts` | `/contacts/` | `contacts:index` |
| WhatsApp Accounts | `whatsapp` | `/whatsapp/` | `whatsapp:index` |
| Agents | `agents` | `/agents/` | `agents:index` |
| Knowledge Base | `knowledge` | `/knowledge/` | `knowledge:index` |
| Team | `organizations` | `/team/` | `organizations:team` |
| Settings | `organizations` | `/settings/` | `organizations:settings` |

Add each `include()` to `config/urls.py`. Overview keeps real content: page header plus a
restrained card grid of the platform areas (no invented metrics).

## Step 8 — Toasts

Keep Django messages → `#toast-container`. Restyle: white/slate-800 surface, left accent
or icon per level (success/error/warning/info), `shadow-lg`, `rounded-lg`, slide+fade in,
auto-dismiss ~5s with hover pause, manual dismiss, `role="alert"` for errors /
`role="status"` otherwise, `aria-live="polite"` container, `prefers-reduced-motion`
respected. Position bottom-right (avoids the navbar/user-menu corner). Works identically
on auth and dashboard pages.

## Step 9 — Docs and agent rules

- Delete `.kilo/skill/green-deck/`.
- Add `.kilo/skill/wazely-ui/SKILL.md`: trigger-rich frontmatter, tokens, type scale,
  spacing/radius/elevation rules, component contracts and include signatures, theming
  mechanism, Tailwind build commands, pinned Alpine/htmx versions, do's and don'ts.
- `.kilo/agent/ui.md`: remove the "no CSS framework" rule, require `wazely-ui`, replace
  `green-deck` in `requirements.skills`.
- `.kilo/agent/django-htmx.md`: swap the `green-deck` reference for `wazely-ui`.
- `.kilo/README.md`: update the skills table row.
- `AGENTS.md`: add the frontend build section (Tailwind binary + commands) and note
  Tailwind/Alpine as frontend dependencies.

## Step 10 — Tests

Update in `apps/accounts/tests.py`: the assertion `data-theme="dark"` becomes `"light"`.
Keep all other existing assertions passing unchanged.

Add `apps/dashboard/tests.py` (and per-app tests where the route lives):
- each of the 8 routes redirects anonymous users to login;
- each renders 200 for an authenticated user and uses `shell.html`;
- navbar/sidebar render the theme toggle and sidebar toggle;
- component gallery view renders via `RequestFactory` (avoids DEBUG/urlconf reload).

## Step 11 — Validation

```powershell
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --minify
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test
.venv\Scripts\python.exe manage.py runserver
```

Manual pass — every page in **both themes** at **3 widths** (≤640, 768–1024, ≥1280):
login, signup, password reset request/sent/confirm/complete, verification sent, email
confirm, logout, account inactive, overview, all 7 placeholder pages, `/ui/` gallery.

Check per page: sidebar collapse persists across navigation; mobile drawer opens/closes
(overlay, `Esc`, scroll lock); dropdowns keyboard-navigable; HTMX invalid login swaps
inline errors without full reload; valid login full-navigates; toast appears after logout;
password visibility toggle works, including after an HTMX swap (Alpine re-init);
focus-visible rings on every interactive element; no unstyled flash on load.

## Risks

- **Alpine + HTMX re-init** — swapped partials lose Alpine bindings without the
  `htmx:afterSwap` → `Alpine.initTree` hook. Verify with the password toggle after a
  failed login.
- **Tailwind source detection** — templates live in two roots (`templates/`,
  `apps/*/templates/`); the explicit `@source` lines above are required or classes get
  purged. Verify built CSS size is non-trivial and spot-check a class used only in an app
  template.
- **Binary not committed** — a fresh clone cannot rebuild CSS until the binary is
  downloaded; mitigated by committing `app.css` and documenting the download.
- **Theme default flip** — light becomes default; the existing dark-default test and any
  hardcoded dark assumptions must be updated.
- **allauth regressions** — the adapter/mixin/URL-name contracts above are easy to break
  while moving templates; the existing 10 tests are the guard.
- **Scope** — 8 new routes across 6 apps plus a component gallery is a wide surface; land
  shell + auth first, then placeholders, then gallery.

## Out of scope

Real features behind the placeholder routes, organization/tenant models, working search,
real notifications, workspace switching, user profile pages, self-hosted fonts, i18n,
CI/deploy build step, and any backend logic changes beyond the placeholder views/URLs.
