# AGENTS.md

This file provides project guidance to AI coding assistants (Claude Code, GitHub Copilot, Cursor,
Codex, etc.) working with this repository. Read it before writing or changing any code.

## Project Overview

ApproveGate — WhatsApp human-in-the-loop approval gateway for autonomous AI agents: risk scoring + tamper-evident audit log.

- **Primary language / stack:** Unknown — fill in the primary language/stack
- **Default branch:** `main`
- **Repository:** https://github.com/matheus24scc/ApproveGate

## Commands

See the project manifest for setup. (No recognized package manager was detected — fill in the real install/build/run commands here.)

> If a command above is missing or wrong, check the project manifest (e.g. `package.json` scripts,
> `Makefile`, `pyproject.toml`) and update this file — keeping AGENTS.md accurate is part of the work.

## Architecture & Conventions

<!-- Fill in as the project grows. Good things to capture here:
  - Where the entry points live and how the main pieces fit together
  - Directory map (what lives where)
  - Non-obvious patterns that diverge from framework defaults
  - State management, data flow, key abstractions
  - Naming/style conventions an agent should follow
-->

- _Describe the high-level architecture here so an agent doesn't have to reverse-engineer it._

## Gotchas & Anti-patterns

<!-- Silent traps that waste an agent's time. Examples:
  - "Don't edit generated files in `dist/` — they're rebuilt by `npm run build`."
  - "This framework version has breaking changes vs. your training data — check the local docs."
-->

- _List the things that have bitten you (or an agent) before._

## Reading Order

When onboarding to this repo, read in this order:
1. `README.md` — what the project is and how to run it
2. This `AGENTS.md` — how to work in it
3. `CONTRIBUTING.md` — contribution workflow and quality gates

## Conventions for Changes

- Follow [Conventional Commits](https://www.conventionalcommits.org/).
- Run the project's lint/test commands before proposing changes.
- Keep this file up to date when you change build steps, structure, or conventions.
