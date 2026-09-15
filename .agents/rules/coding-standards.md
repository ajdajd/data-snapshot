---
trigger: always_on
---

# Coding Standards — Data Snapshot Extraction

To ensure consistency and maintainability across the codebase, all contributors (including AI agents) must adhere to the following standards.

## 1. Python Formatting

- **Formatter**: Mandatory use of **Black**.
- **Line Length**: Default Black behavior (88 characters).
- **Codex command**: In the Codex sandbox, invoke the locked formatter as
  `.venv/bin/black` directly and pass exactly one file per invocation. Do not
  use `uv run` for Black and do not pass multiple files or directories; `uv`
  accesses its read-only shared cache, while Black's multi-file process pool
  does not shut down reliably in the sandbox. For a repository-wide check, use
  `git ls-files -z '*.py' | xargs -0 -n 1 .venv/bin/black --check`.

## 2. Documentation

- **Standard**: All Python code must use the **NumPy docstring standard**.
- **Requirement**: Public modules, classes, and functions must include a descriptive docstring.
- **Content**:
    - **Summary**: A concise one-line summary of the object's purpose.
    - **Parameters**: (If applicable) Names, types, and descriptions of all arguments.
    - **Returns**: (If applicable) Type and description of the return value.
    - **Raises**: (If applicable) Any exceptions that are explicitly raised.

## 3. Type Hinting

- **Mandatory**: All function signatures should include type hints for parameters and return values.
- **Style**: Use modern Python 3.10+ type hinting (e.g., `list[str]` instead of `List[str]`, `str | None` instead of `Optional[str]`).

## 4. Code Structure

- **Naming**: Follow PEP 8 (snake_case for functions/variables, PascalCase for classes).
- **Constants**: Define project-wide constants in `src/data_snapshot/constants.py`.

## 5. Development Environment

- **uv**: All commands and script executions must be performed using `uv run` (e.g., `uv run python -m data_snapshot.evaluation.evaluate_model`). Never use bare `python` without the `uv run` prefix.
- **Black exception**: The direct `.venv/bin/black` command above is the only
  exception to the `uv run` requirement.
