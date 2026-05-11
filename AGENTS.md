# placement-client — Agent Instructions

Python client for obtaining Placement Tokens via OAuth2 Device Flow for HTCondor remote submission.

## Setup

Uses `uv` for package management with a `.venv` virtual environment.

```bash
uv venv
uv pip install -e ".[dev,test,jupyter]"   # editable install with dev + test + jupyter extras
```

The `htcondor2` binding is the sole runtime dependency. The Jupyter module additionally requires `ipywidgets` and `IPython` (optional, guarded by `try/except ImportError` at module level).

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

| File | Responsibility |
|---|---|
| `placement_client/__init__.py` | Public API: `DeviceClient`, `DeviceClientError`, `request_token`, `request_token_and_return`, `write_token` |
| `placement_client/cmd.py` | CLI entry point (`placement-request`) → `cmd:main` |
| `placement_client/common.py` | Token file I/O, `TokenState` enum, `get_condor_tokens_dir`, permissions |
| `placement_client/device.py` | OAuth2 Device Flow (`DeviceClient`). Stdlib only (`urllib`). |
| `placement_client/text_ui.py` | Interactive console helpers for device flow |
| `placement_client/jupyter.py` | ipywidgets UI; requires `ipywidgets` + `IPython` |

Dependency direction: UI layers (`text_ui.py`, `jupyter.py`, `cmd.py`) depend on core (`device.py`, `common.py`), never the reverse.

## Key Conventions

- **Logging**: Every module uses `_log = logging.getLogger(__name__)`. No `print()` in library code; user-facing output lives only in `text_ui.py` and `jupyter.py`.
- **Exceptions**: Typed hierarchy in `device.py` rooted at `DeviceClientError`. HTCondor errors are `htcondor2.HTCondorException`.
- **Token security**: Token files written with `0o600`; tokens directory created with `0o700`. Filename validation rejects `/`, `\`, `:`.
- **Python compat**: Target is >= 3.6.8.

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
