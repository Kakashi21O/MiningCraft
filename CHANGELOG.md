# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-05

### Added

- Python project configuration via `pyproject.toml` (Hatch build, Python 3.12+)
- Ruff configuration for linting and formatting
- mypy strict type checking configuration
- pytest, pytest-asyncio, and pytest-mock test configuration
- `src/` package layout with layer skeletons (protocol, core, perception, decision, action, modules, models)
- `tests/` skeleton layout mirroring the package structure
- `config/config.yaml` and `config/logging.yaml` templates
- GitHub Actions CI workflow (Ruff, mypy, pytest)
- GitHub issue templates, PR template, and CODEOWNERS
- `CLAUDE.md` agent instructions
