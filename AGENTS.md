# placement-client — Agent Instructions

Python client for obtaining Placement Tokens via OAuth2 Device Flow for HTCondor remote submission.

## Setup

Uses `uv` for package management with a `.venv` virtual environment.

```bash
uv venv
uv pip install -e ".[dev,test,jupyter]"   # editable install with dev + test + jupyter extras
```

The `htcondor` package (providing the `htcondor2` module) is the sole runtime dependency. Jupyter support is provided via the `jupyter` extra (`ipython`, `ipywidgets`), matching the notebook UI module imports.

## Commands

| Command | Purpose |
|---|---|
| `uv run pytest` | Run all tests |
| `uv run pytest tests/test_common.py` | Run specific test file |
| `uv run black -S placement_client tests` | Format code |
| `uv run isort --profile=black placement_client tests` | Sort imports |
| `uv run placement-request <hostname>` | Run CLI entry point |

## Package Structure

All source lives under `placement_client/` (underscore, not dash).

| File | Responsibility | Depends On |
|---|---|---|
| `placement_client/__init__.py` | Public API: `DeviceClient`, `DeviceClientError`, `request_token`, `request_token_and_return`, `write_token` | `.common`, `.device`, `.err`, `.text_ui` |
| `placement_client/cmd.py` | CLI entry point (`placement-request`) → `cmd:main` | `placement_client.common`, `placement_client.text_ui` |
| `placement_client/common.py` | Token file I/O, `TokenState` enum, `get_condor_tokens_dir`, permissions | None (Stdlib) |
| `placement_client/device.py` | Core OAuth2 Device Flow client logic for token acquisition. Stdlib only (`urllib`). | `.err` |
| `placement_client/err.py` | Exception hierarchy rooted at `DeviceClientError`. | None |
| `placement_client/text_ui.py` | Interactive console helpers for device flow | `placement_client.common`, `placement_client.device` |
| `placement_client/jupyter.py` | ipywidgets UI; requires `ipywidgets` + `IPython` | `placement_client.common`, `placement_client.device`, `ipywidgets`, `IPython` |

Dependency direction: UI layers (`text_ui.py`, `jupyter.py`, `cmd.py`) depend on core (`device.py`, `common.py`), never the reverse.

## Context Anchors

1. `placement_client/device.py`: Heart of the OAuth2 Device Flow implementation.
2. `placement_client/common.py`: Token state and HTCondor filesystem integration.
3. `placement_client/text_ui.py`: Terminal UX orchestration for token requests.

## Key Conventions

- **Logging**: Prefer `_log = logging.getLogger(__name__)` for library diagnostics (used by core modules such as `common.py` and `device.py`). User-facing output primarily lives in `text_ui.py` and `jupyter.py`; `common.describe_token` also emits user-facing text.
- **Exceptions**: Typed hierarchy in `err.py` rooted at `DeviceClientError`. HTCondor errors are `htcondor2.HTCondorException`.
- **Token security**: Token files written with `0o600`; tokens directory created with `0o700`. Filename validation rejects `/`, `\`, `:`.
- **Python compat**: Target is >= 3.6.8.
- **Core HTTP client**: Keep networking in `device.py` on stdlib `urllib` (avoid adding `requests` there).

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `PLACEMENT_WEBAPP_LINK` | Placement Webapp base URL | `http://localhost:5000` |
| `DEVICE_CLIENT_ID` | Client ID for device flow | `placement_client` |
| `SEC_TOKEN_DIRECTORY` (HTCondor param) | Token directory path | `~/.condor/tokens.d/` |

## Testing Notes

- `tests/conftest.py` adds the repo root to `sys.path`.
- `test_optional_dependencies.py` skips if `htcondor2`, `ipywidgets`, or `IPython` are unavailable (uses `pytest.importorskip`).
- `test_common.py` monkeypatches `get_condor_tokens_dir` and `time.time` — no live HTCondor needed.
