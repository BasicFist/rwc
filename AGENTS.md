# Repository Guidelines

## Project Structure & Module Organization
- `rwc/core`: model loading, voice conversion pipeline, reusable DSP helpers.
- `rwc/cli` and `rwc/tui*.py`: command-line and TUI entry points; the `rwc` console script resolves here.
- `rwc/api` and `rwc/webui.py`: Flask API and Gradio UI surfaces for remote and browser-driven control.
- `rwc/utils`: shared utilities (audio I/O, configuration, logging).
- `models/` stores downloaded checkpoints and indexes; keep large assets out of git.
- `scripts/` and top-level `start_*.sh` wrappers automate environment startup—update them when CLI options change.

## Build, Test, and Development Commands
- `python3 -m venv venv && source venv/bin/activate`: create or reuse the standard virtual environment.
- `pip install -e .[dev]`: editable install with pytest, black, flake8, and mypy tooling.
- `rwc serve-webui --port 7865`: launch the Gradio interface for manual regression checks.
- `python -m pytest`: execute the test suite; add `-k pattern` for targeted runs.
- `bash download_models.sh`: sync baseline checkpoints before validating conversion paths.

## Coding Style & Naming Conventions
- Use 4-space indentation, type hints for new Python code, and keep functions focused (<150 lines).
- Format with `black rwc rwc/tests` (line length 88) and lint via `flake8 rwc`.
- Adopt snake_case for modules and functions, UpperCamelCase for classes, and kebab-case for shell scripts.
- Align CLI verbs with existing patterns (`convert`, `serve-*`) to keep UX consistent.

## Testing Guidelines
- Place tests in `rwc/tests`; name modules `test_*.py` and functions `test_*`.
- Mock GPU-intensive paths when feasible; prefer fixture-driven unit tests over long-running conversions.
- Document assumptions inside tests and measure coverage for new logic paths before merging.

## Commit & Pull Request Guidelines
- Write imperative, capitalized commit subjects (e.g., `Add real-time TUI polling`); add body details for context and rollbacks.
- Reference related issues (`Fixes #123`) and call out key scripts or configs touched.
- Pull requests should summarize behavior changes, enumerate test commands run, and attach screenshots for UI updates.

## Security & Configuration Notes
- Never commit credentials, personal voice data, or large checkpoints (ensure `.gitignore` stays current).
- Update `config.ini` defaults cautiously and mirror changes in `README.md` and `SECURITY.md` when deployment steps shift.
