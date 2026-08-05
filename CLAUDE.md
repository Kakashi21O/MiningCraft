# CLAUDE.md

Guidance for Claude Code and other AI agents working in this repository.

## Project

MiningCraft is a modular Python automation framework for Minecraft Java Edition.
It is deterministic and rule-based — not an ML or LLM-controlled bot.

## Before You Start

Read the project context files in `context/` before any work. They define the
authority hierarchy, architecture, and process. Start with:

1. `context/03_AGENT_SYSTEM.md` — roles, authority, pipeline
2. `context/09_DECISIONS.md` — recorded decisions (ADRs)
3. `context/01_ARCHITECTURE.md` — architecture specification
4. `context/07_ROADMAP.md` — roadmap and current phase
5. `context/05_CODE_RULES.md` — engineering standards
6. `context/10_PROGRESS.md` — current status tracker

## Commands

- Lint: `ruff check .`
- Format: `ruff format .` (verify with `ruff format --check .`)
- Type check: `mypy src/`
- Test: `pytest`

## Rules

- Never commit to `master` or `develop` directly.
- Work on a `feature/<name>` branch with at least 5 meaningful commits.
- Use Conventional Commits (see `context/02_GIT_WORKFLOW.md`).
- Dependencies flow downward only (see `context/01_ARCHITECTURE.md`).
- Never use `print()`; use `structlog`.
- Never hardcode config values; use `config/config.yaml`.
- Keep functions under ~50 lines and type hint every public function.

## Conventions

- Python 3.12+, async-first
- Build: Hatch (`pyproject.toml`, no `setup.py`)
- Layered src layout: `src/miningcraft/{protocol,core,perception,decision,action,modules,models}`
- Tests in `tests/` mirror the package layout; all tests run without a Minecraft server

## Note

`context/` is gitignored and local-only by design. The progress tracker
(`context/10_PROGRESS.md`) is updated locally and is not committed.
