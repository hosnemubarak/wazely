# Kilo Agents and Skills

Version-controlled AI coding helpers for this Wazely project. They ship with the repo
so every teammate uses the same roles and reference material.

## The three file types

| File | What it is | When it loads |
|---|---|---|
| `AGENTS.md` (repo root) | Rules that always apply | **Always.** Every session. |
| `.kilo/agent/*.md` | A role, e.g. "Django backend" | **When you select it.** One at a time. |
| `.kilo/skill/<name>/SKILL.md` | Knowledge a role can look up | **When it matches your task.** |

## Agent vs skill

- An **agent** is *who is working*. Pick one per task. It is a role with its own rules
  and tools. Only one primary agent runs at a time.
- A **skill** is *what the worker knows*. It is a reference file the agent reads when
  the task matches. Any agent can read any skill.

Think of a job: the agent is the worker you hire, the skill is a manual on the shelf
they consult.

## How to use them

**Pick an agent.** Tell Kilo who should do the work, up front:

```
I need to write a Django migration. Use the django agent.
"Write the user profile model. django agent."
```

Or switch in the session menu: `/agents`, then pick `django-htmx` or `ui`.

**Use subagents for scoped work.** The `code-reviewer` and `github-workflow` agents are
subagents invoked from another agent. Tell the primary agent to use them:

```
django-htmx agent: implement the message model, then ask code-reviewer to review the diff.
```

## Current files

### Agents (.kilo/agent/)

| File | Role |
|---|---|
| `django-htmx.md` | Full stack Django + HTMX: models, views, templates, forms, HTMX partials |
| `ui.md` | Design decisions: layout, color, components, accessibility |
| `data.md` | Notebook-first data analysis (existing) |
| `code-reviewer.md` | Subagent that reviews code for standards and bugs |
| `github-workflow.md` | Subagent that handles commits, branches, and PRs |

### Skills (.kilo/skill/<name>/SKILL.md)

| Skill | Use for |
|---|---|
| `django-models` | Fat models, thin views, QuerySet optimization |
| `django-forms` | ModelForm, validation, clean methods, HTMX forms |
| `django-templates` | Inheritance, partials, tags, filters |
| `django-extensions` | Introspecting URLs, models, settings; shell_plus |
| `htmx-patterns` | Partial views, hx- attributes, dynamic UI without JS |
| `celery-patterns` | Background tasks, retries, idempotency, beat schedules |
| `pytest-django-patterns` | Test factories, fixtures, TDD workflow |
| `code-quality` | Running ruff, pyright, and reporting by severity |
| `systematic-debugging` | Four-phase debugging with root-cause analysis |
| `docs-sync` | Verify docs match code |
| `onboard` | Building context for a new task or feature |
| `pr-review` | Reviewing a pull request against project standards |
| `pr-summary` | Generating a PR description from branch changes |
| `ticket` | Working end-to-end on a JIRA/Linear ticket |
| `worktree-commit-merge` | Committing and merging an Agent Manager worktree |
| `skill-creator` | Writing a new skill file the right way |

## Required frontmatter

**Agents** only need a description so you can pick the right one:

```yaml
---
description: what this role does
mode: primary   # primary = selectable. subagent = invoked by other agents
---
```

`mode` is optional. If omitted, Kilo applies a sensible default.

**Skills** need a `name` and a trigger-rich `description`. This is the only part Kilo
reads before loading the full file, so make it keyword-dense:

```yaml
---
name: my-skill
description: Use when <task>. Triggers: word1, word2, word3.
---
```

A skill must live in a **folder** as `SKILL.md`:

```
.kilo/skill/<name>/SKILL.md
```

A flat file like `.kilo/skill/my-skill.md` is ignored.

## Naming note

- Project Django apps live under `apps/` (e.g. `apps/agents/` for AI customer agents).
- Kilo helper files live under `.kilo/`.
- To avoid confusion: the `django-htmx.md` helper is a coding role; the `apps/agents`
  folder is application data. They are unrelated.

## Git

Commit everything under `.kilo/` and the root `AGENTS.md`:

```
git add AGENTS.md .kilo/
git commit -m "Update Kilo agents and skills"
```

`.kilo/.gitignore` excludes local state:

```
worktrees/
agent-manager.json
kilo.local.json
```

Do **not** commit personal settings (model choice, theme, API keys). Those live in
`~/.config/kilo/`.

## Note

If you rename or move a folder inside `.kilo/` while Kilo is running and see
`Failed to parse frontmatter`, just reload the window. The files are fine.
