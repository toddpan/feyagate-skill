# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`feyagate-skill` is a Python PyPI package that acts as a CLI installer and wrapper around a pre-built Go binary (`miloco-mcp-server`). The Python code handles download, install, start/stop, and AI agent integration. The actual MCP smart home logic lives in the binary, not in this repo. Python modules communicate with the Go binary exclusively via HTTP JSON-RPC calls through `mcp.py`.

## Commands

**Development install:**
```bash
pip install -e ".[dev]"
```

**Run tests:**
```bash
pytest                          # all tests
pytest tests/test_cli.py        # single file
pytest tests/test_cli.py::TestClass::test_method  # single test
```

**Build package:**
```bash
bash scripts/build.sh           # produces dist/
```

**Publish to PyPI:**
```bash
PYPI_TOKEN=xxx bash scripts/publish.sh pypi       # production
TEST_PYPI_TOKEN=xxx bash scripts/publish.sh testpypi  # staging
```

## Architecture

```
feyagate_skill/
  cli.py        # argparse entry point; routes subcommands to modules below
  installer.py  # fetches fota.json from FOTA_URL, downloads binary archive, extracts to ~/.feyagate/
  service.py    # start/stop/status of miloco-mcp-server binary via PID file
  config.py     # loads ~/.feyagate/config/config.yaml (YAML, never raises)
  auth.py       # Xiaomi/Mi Home OAuth flow via HTTP to running MCP server
  mcp.py        # HTTP client for calling MCP server tools (sync + optional async via aiohttp)
  snapshot.py   # camera snapshot via mcp.py
  scheduled.py  # recurring camera capture loop
  data/         # bundled files copied to ~/.feyagate on setup: SKILL.md, skills/*.md, config.yaml.example
```

**Runtime layout** (installed at `~/.feyagate/` by default):
- `bin/miloco-mcp-server` — the actual MCP server binary
- `config/config.yaml` — server config (HTTP port 38080, WS port 8765)
- `data/miloco-mcp-server.pid` — PID file used by service.py
- `data/miloco-mcp-server.log` — server log
- `lib/` — shared libraries; symlinked into `bin/lib` for rpath

**AI agent skill installation** (`feyagate install-<agent>`): creates a symlink from `~/<agent-dir>/skills/feyagate` → `~/.feyagate/`. This exposes `SKILL.md` and `skills/*.md` to the agent.

Agent symlink targets per agent:
- `install-claude` → `~/.claude/skills/feyagate`
- `install-cursor` → `~/.cursor/skills/feyagate`
- `install-openclaw` → `~/.openclaw/skills/feyagate`
- `install-hermes` → `~/.hermes/skills/feyagate`
- `install-windsurf` → `~/.codeium/windsurf/skills/feyagate`
- `install-copilot` → platform-dependent VS Code dir + `/skills/feyagate`
- `install-codex` → `~/.codex/skills/feyagate`

## Key conventions

- **Lazy imports in cli.py**: subcommand modules (`installer`, `service`, `auth`, etc.) are imported inside the `elif` branches, not at module top. This keeps CLI startup fast.
- **config.py never raises**: `load_config()` returns `{}` on any error (missing file, YAML parse error, etc.). Callers can safely index the result without try/except.
- **mcp.py dual interface**: `mcp_call()` is synchronous (stdlib `urllib`), `async_mcp_call()` uses `aiohttp` (optional dependency). Both target `POST /mcp/http` on the Go binary using JSON-RPC 2.0.
- **service.py process lifecycle**: managed via a PID file (`miloco-mcp-server.pid`). Start spawns the binary with `subprocess.Popen`, stop sends SIGTERM then SIGKILL after 5s timeout.
- **installer.py FOTA flow**: fetches `fota.json` → matches platform via `FOTA_TYPE_MAP` → downloads archive → verifies MD5 → extracts binary + libs + webui to `~/.feyagate/`.
- **Two copies of every SKILL doc must be kept in sync**:
  - The repo source at `SKILL.md` and `skills/<name>.md` (for repo browsing / source installs).
  - The package-bundled copy at `feyagate_skill/data/SKILL.md` and `feyagate_skill/data/skills/<name>.md`, which `installer._copy_skill_docs()` copies into `~/.feyagate/` on `feyagate setup`. `_copy_skill_docs()` only writes files that don't already exist at the target — so an upgrade of the Python package will not overwrite an older copy in `~/.feyagate/`. After editing the source SKILL docs, always `cp` them to the `feyagate_skill/data/` mirror before publishing.
- **MCP tool names and parameter casing**: device control tools (`device/specs`, `set_*`, `get_*`, `execute_*`) all use `deviceId` (camelCase); only `xiaoai/*` (tts/control/play_music) uses `device_id` (snake_case). The full canonical list lives in `app/miloco-mcp-server/src/mcp/mcp_tools.cpp` — if you change a tool name or schema there, update the corresponding sub-skill in this repo to match.

## Key constants

All in `feyagate_skill/__init__.py`:
- `DEFAULT_INSTALL_DIR = "~/.feyagate"`
- `FOTA_URL` — FOTA server endpoint for binary release metadata
- `MCP_DEFAULT_PORT = 38080`
- `MCP_DEFAULT_HOST = "127.0.0.1"`

## Version management

The version string exists in **two places** and must be kept in sync manually:
1. `feyagate_skill/__init__.py` — `__version__`
2. `pyproject.toml` — `version`

Bump both before building and publishing.

## MCP server endpoints

When running, `miloco-mcp-server` exposes:
- `GET /health` — health check (used by `service.py` startup wait loop)
- `POST /mcp/http` — MCP tool calls (JSON-RPC 2.0)
- `GET /` — WebUI dashboard

## Testing patterns

Tests use `pytest` with `unittest.mock`. Key patterns:
- Filesystem-dependent tests use `tmp_path` fixture and monkeypatch `DEFAULT_INSTALL_DIR` and `Path.home()`.
- Tests that invoke CLI subcommands patch the corresponding `_install_*` function and check it was called, or patch `sys.argv` and call `main()`.
- No integration tests that hit a real MCP server — all MCP calls are mocked or skipped.

## Gotchas

- `feyagate update` (alias: `upgrade`, hidden, kept for backward compatibility) is an alias for `feyagate setup` — both call `installer.do_setup()`.
- `--port` on `start`/`restart` only affects the health-check URL used during startup. The binary always reads its actual listening port from `config.yaml`. To change the port, edit `~/.feyagate/config/config.yaml`.
- The `scripts/` directory contains both build/publish shell scripts (`build.sh`, `publish.sh`) and standalone Python utility scripts (`snapshot.py`, `auth.py`, `scheduled_analysis.py`) that are not part of the package — they are developer tools.
