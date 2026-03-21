# meso_negotiator

## What This Is

Meso-level negotiation assistant — a Python backend with a React TypeScript frontend.

## Commands

- `mise run setup` — Create venv and install Python dependencies
- `mise run lint` — Run all linters (ruff + biome)
- `mise run lint:fix` — Auto-fix lint issues
- `mise run format` — Auto-format all files (ruff + biome)
- `mise run test` — Run pytest
- `mise run typecheck` — Run mypy + tsc
- `mise run check` — Lint + test

## Git Conventions

- Conventional Commits: `<type>(<scope>): <description>`
- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Imperative mood, lowercase, no period, 50 char subject limit
- See `~/.claude/skills/git-workflow/references/conventional-commits.md`

## Project Structure

```
meso_negotiator/
├── mise.toml          — Tool versions and task runner
├── pyproject.toml     — Python project metadata
├── ruff.toml          — Python linter config
├── biome.json         — JS/TS linter + formatter config
├── CLAUDE.md          — This file
├── back/              — Python backend
│   └── tests/         — Python tests (pytest)
└── front/             — React TypeScript frontend
```

## Stack

- **Python 3.12** via mise, managed with uv
- **React + TypeScript** for the frontend
- **ruff** — Python linting and formatting
- **biome** — JS/TS linting and formatting
- **pytest** — Python tests
- **mypy** — Python type checking (strict)

## Notes

- Shell is nushell — avoid `&&` in shell commands, use `;` instead
- Run `mise trust` once after cloning to activate tool versions
- Run `mise install` to download all tools
- Run `mise run setup` to create the Python venv
