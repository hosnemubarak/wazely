---
name: wazely-ui
description: Wazely UI — the Tailwind v4 design system for this project. Use for ALL UI work: building or styling any page, partial, HTMX fragment, form, component, or stylesheet; theming and dark mode; sidebar, navbar, auth, toast, or empty-state patterns. Triggers: UI, design, design system, style, styling, CSS, Tailwind, color, colour, typography, font, spacing, layout, component, button, card, input, badge, table, dropdown, modal, toast, alert, spinner, tooltip, empty state, sidebar, navigation, navbar, search, theme, dark mode, light mode, restyle, skin, brand, emerald.
---

# Wazely UI — Tailwind v4 Design System

Wazely is a B2B SaaS product: light-first, emerald identity, Inter type,
slate neutrals, restrained elevation, sentence-case labels. Dark mode is a
first-class theme driven by `<html data-theme="dark">`.

Applies to every screen: dashboard shell, auth pages, placeholder pages, HTMX
partials, and the component gallery alike.

## Stack and build

- **Tailwind CSS v4** via the standalone `bin/tailwindcss.exe` binary (Windows
  x64, downloaded from `tailwindlabs/tailwindcss` releases; **not committed** —
  `.gitignore` has `bin/`). Source: `static/css/app.src.css`. Built file:
  `static/css/app.css` (**committed**; `collectstatic` picks it up).

```powershell
# download once per machine (check the latest v4 release)
Invoke-WebRequest https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe -OutFile bin\tailwindcss.exe

.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --watch   # dev
.\bin\tailwindcss.exe -i static/css/app.src.css -o static/css/app.css --minify  # before commit
```

- **Alpine.js 3.15.0** vendored at `static/js/alpine.min.js`, loaded `defer`
  after `app.js` and `htmx.min.js`.
- **HTMX 2.0.6** vendored at `static/js/htmx.min.js`.
- `static/js/app.js` — theme toggle, sidebar collapse, toast lifecycle,
  `wzPassword` component, and the `htmx:afterSwap` → `Alpine.initTree` hook
  (required: swapped auth partials contain Alpine components).
- Fonts: Inter (variable) + JetBrains Mono from Google Fonts.

If you edit classes in any template under `templates/` or `apps/*/templates/`,
rebuild `app.css` — Tailwind only emits classes it can see in those roots
(declared via `@source` in `app.src.css`).

## Tokens

Brand ramp (emerald): `brand-50 #ecfdf5` → `brand-500 #10b981` →
`brand-600 #059669` (primary) → `brand-700 #047857` (hover) →
`brand-900 #064e3b` → `brand-950 #022c22`. Use them as `bg-brand-600`,
`text-brand-700`, `dark:text-brand-400`, etc.

- Neutrals: built-in `slate`.
- Semantic: success `brand-600` (icon `brand-400` on dark), warning
  `amber-500`, error `red-600` (dark `red-400`), info `sky-600` (dark
  `sky-400`).
- Font: `font-sans` = Inter, `font-mono` = JetBrains Mono.
- Gradients: **only** the auth brand panel (`bg-linear-to-br from-brand-800
  via-brand-900 to-brand-950`). Nothing else.

## Type scale

| Role | Classes |
|---|---|
| Auth headline | `text-3xl font-semibold tracking-tight` |
| Page title | `text-2xl font-semibold tracking-tight` |
| Section | `text-lg font-semibold` |
| Card title | `text-sm font-semibold` |
| Body | `text-sm` |
| Secondary | `text-sm text-slate-500 dark:text-slate-400` |
| Label | `text-xs font-medium` (sentence case — no uppercase tracking) |
| Nav item | `text-sm font-medium` |
| Button | `text-sm font-medium` |
| Meta | `text-xs` |

## Spacing, radius, elevation

- Radius: `rounded-md` controls/buttons/inputs, `rounded-lg` cards/panels/
  dropdowns/toasts, `rounded-full` avatars/badges only. No larger radii.
- Elevation: borders first — `border-slate-200 dark:border-white/10`;
  `shadow-xs` on cards/inputs; `shadow-lg` only for popovers, dropdowns,
  modals, toasts.
- Page content: `px-6 py-8 lg:px-8` inside `<main>`; cards `p-6`; gaps `gap-6`.

## Theming

- Default is **light**. `<html data-theme="light">` is the static default.
- An inline script in `base.html` runs before first paint:
  `localStorage["wazely-theme"]` → `prefers-color-scheme` (dark only when the
  OS prefers dark) → light. No flash of the wrong theme.
- `@custom-variant dark` maps `dark:` utilities to
  `[data-theme="dark"], [data-theme="dark"] *`.
- Toggle: any element with `data-theme-toggle` (see
  `partials/_theme_toggle.html`, included in the navbar and on auth screens).
  `app.js` flips the attribute and persists the choice.
- Sidebar collapse works the same way: `<html data-sidebar="collapsed">`,
  persisted as `localStorage["wazely-sidebar"]`, toggled by any element with
  `data-sidebar-toggle`. CSS in `app.src.css` reacts to the attribute, so
  there is no flash on load.
- Never hardcode a color that exists as a token; never add hex values to
  templates.

## Component contracts

Component primitives live in `templates/components/`. Include signatures:

```django
{% include "components/_button.html" with text="Save" variant="primary" type="submit" %}
{% include "components/_button.html" with text="Delete" variant="danger" disabled=True %}
{% include "components/_input.html" with id="email" name="email" label="Email" type="email" help="..." error="..." %}
{% include "components/_card.html" with title="..." subtitle="..." body="..." %}
{% include "components/_badge.html" with text="Coming soon" variant="muted" %}
{% include "components/_table.html" with headers=table_headers rows=table_rows %}
{% include "components/_empty_state.html" with icon="inbox" title="..." description="..." action_text="..." action_url="..." %}
{% include "components/_dropdown.html" with label="Options" items=dropdown_items %}
{% include "components/_modal.html" with open_text="Open" title="..." body="..." action_text="Confirm" %}
{% include "components/_alert.html" with variant="error" title="..." text="..." %}
{% include "components/_toast.html" with variant="success" text="..." %}
{% include "components/_spinner.html" %} {# optional size="24" #}
{% include "components/_tooltip.html" with label="..." content="Hover me" %}
{% include "components/_icon.html" with name="settings" %} {# optional size, icon_class #}
```

- Badge/alert/toast variants: `success`, `warning`, `error`, `info`, `muted`
  (badge only).
- Icon names: `layout-dashboard`, `message-circle`, `user`, `users`, `phone`,
  `bot`, `book-open`, `settings`, `log-out`, `menu`, `panel-left`, `search`,
  `bell`, `chevron-down`, `check`, `x`, `eye`, `eye-off`, `alert-triangle`,
  `info`, `check-circle`, `x-circle`, `inbox`, `mail`, `plus`. Inline SVGs
  (Lucide paths) — no icon package.
- CSS component classes (defined once in `app.src.css` with `@apply`):
  `.btn` + `.btn-primary|secondary|ghost|danger`, `.input`, `.card`,
  `.badge-*`, `.nav-item` (+ `[aria-current="page"]` active state), `.sidebar`,
  `.sidebar-label`, `.sidebar-tip`, `.sidebar-item`, `.sidebar-center`,
  `.main-shell`, `.toast`, `.toast-close`, `.toast-icon-*`, `.spinner`,
  `.tooltip`, `.modal`. Everything else is utilities in templates.
- Dropdowns: Alpine `x-data="{ open: false }"` + `@click.outside` +
  `@keydown.escape.window`, `:aria-expanded`, `aria-haspopup="true"`, menu is
  `x-cloak x-show="open"` with `origin-top-right` transition classes.
- Modals: native `<dialog>` driven by Alpine `$refs` — focus trap and Esc for
  free; click on the backdrop closes (`@click="if ($event.target === $el) $el.close()"`).

**Component gallery**: `ComponentGalleryView` at `/ui/` (DEBUG only) is the
manual QA surface for every component in both themes. Keep it updated when a
component changes.

## Layouts

- `base.html` — html/head, FOUC-prevention script, fonts, `app.css`, skip
  link, `#toast-container`, scripts (`app.js` → `htmx.min.js` →
  `alpine.min.js`, all `defer`). Blocks: `title`, `body`, `extra_css`,
  `extra_js`. Body carries `hx-headers` CSRF.
- `shell.html` — authenticated app shell: off-canvas overlay, sidebar,
  navbar, `<main>`. Blocks: `page_header`, `breadcrumb`, `page_title`,
  `page_actions`, `content`. (Blocks render inside `main`; the navbar is
  include-rendered and cannot carry child blocks.)
- `partials/_sidebar.html` — groups: Overview / Workspace (Conversations,
  Contacts, WhatsApp Accounts) / AI (Agents, Knowledge Base) / Management
  (Team, Settings). `w-64` ↔ `w-16` collapse, tooltips when collapsed, user
  block + logout at the bottom. Below `lg`: off-canvas drawer with overlay,
  Esc to close, body scroll lock.
- `partials/_navbar.html` — sidebar toggles, disabled search with "Coming
  soon" tooltip, notifications dropdown (empty state), theme toggle, user
  menu (email, Settings, Log out). No workspace switcher.
- `account/base.html` — auth split shell: form column (`max-w-sm`, vertically
  centered) + emerald brand panel (`hidden lg:flex`, gradient, value prop +
  3 proof points). Single column with compact brand header below `lg`.

## Forms and toasts

- `partials/_form_fields.html` renders Django forms: labels (`text-xs
  font-medium`), non-field errors (`.form-errors`, `role="alert"`), per-field
  errors (`.field-error`, id `{field_id}_error` — Django 4.1+ automatically
  sets `aria-invalid="true"` and `aria-describedby="{field_id}_error"` on the
  widget, so keep those ids exact), help text (id `{field_id}_helptext` to
  match Django's automatic `aria-describedby`), and the Alpine password
  visibility toggle (`x-data="wzPassword"`) for password widgets.
- Auth form partials keep the HTMX contract: `#auth-form` swap target,
  `hx-post`/`hx-target`/`hx-swap="outerHTML"`, `hx-indicator="#auth-submit-indicator"`,
  `hx-disabled-elt="find button[type='submit']"`, spinner inside the submit
  button.
- Toasts: Django messages render through `partials/_messages.html`, which
  includes `components/_toast.html` per message, into `#toast-container`
  (bottom-right, `aria-live="polite"`). Styling is CSS-only (`.toast-*` in
  `app.src.css`): slide+fade in, auto-dismiss ~5s paused on hover, manual
  dismiss via `[data-toast-close]`, `role="alert"` for errors /
  `role="status"` otherwise; `prefers-reduced-motion` disables animation and
  `app.js` falls back to a plain ~5s auto-dismiss timer.

## Do's and Don'ts

- Do default to light styling and add `dark:` utilities for dark mode.
- Do use `focus-visible:outline-2 focus-visible:outline-offset-2
  focus-visible:outline-brand-600` on every interactive element.
- Do use sentence case for labels, buttons, and headings — no uppercase
  tracking.
- Do keep copy short and scannable; `text-sm` is the workhorse size.
- Don't invent colors — use the brand ramp and slate; semantic colors only
  for their meaning.
- Don't add gradients, large shadows, or oversized radii (see rules above).
- Don't write raw CSS for new UI — utilities in templates, `@apply` component
  classes in `app.src.css` for high-churn primitives only.
- Don't use `alert()`/`confirm()` — use toasts and the modal component.
- Don't fake data: empty states stay empty, search stays disabled until real.
- Don't skip rebuilding `app.css` after adding classes, and commit the built
  file.
