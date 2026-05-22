"""Shared MCP API helper — sync and async."""

import asyncio
import json
import logging
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synchronous MCP call
# ---------------------------------------------------------------------------


def mcp_call(host: str, port: int, tool: str, arguments: dict | None = None) -> dict:
    """Call an MCP tool via the HTTP JSON-RPC endpoint (sync).

    Args:
        host: MCP server host.
        port: MCP server HTTP port.
        tool: Tool name (e.g. ``"xiaomi/get_properties"``).
        arguments: Tool arguments dict (optional).

    Returns:
        Parsed result dict, or ``{"error": "..."}`` on failure.
    """
    url = f"http://{host}:{port}/mcp/http"
    payload = _build_payload(tool, arguments)
    headers = {"Content-Type": "application/json"}
    try:
        req = Request(url, data=payload, headers=headers)
        with urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except URLError as exc:
        logger.error("MCP connection failed for %s: %s", tool, exc)
        return {"error": f"Connection failed: {exc}"}
    except OSError as exc:
        logger.error("MCP network error for %s: %s", tool, exc)
        return {"error": f"Network error: {exc}"}

    return _parse_response(raw, tool)


# ---------------------------------------------------------------------------
# Async MCP call (aiohttp-based, optional)
# ---------------------------------------------------------------------------

_aiohttp_client = None
_AIOHTTP_AVAILABLE = False

try:
    import aiohttp as _imported_aiohttp
    _AIOHTTP_AVAILABLE = True
except ImportError:
    pass


def _build_payload(tool: str, arguments: dict | None) -> bytes:
    """Build JSON-RPC 2.0 request body."""
    return json.dumps({
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    }).encode("utf-8")


def _parse_response(raw: bytes, tool: str = "<unknown>") -> dict:
    """Parse JSON-RPC response body."""
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("MCP invalid JSON response for %s: %s", tool, exc)
        return {"error": f"Invalid JSON response: {exc}"}

    if "error" in result:
        return result

    try:
        text = result["result"]["content"][0]["text"]
        return json.loads(text)
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.error("MCP unexpected response structure for %s: %s", tool, exc)
        return result


async def async_mcp_call(
    host: str,
    port: int,
    tool: str,
    arguments: dict | None = None,
    timeout: int = 30,
) -> dict:
    """Call an MCP tool via HTTP (async, requires ``aiohttp``).

    When ``aiohttp`` is not installed this returns
    ``{"error": "aiohttp not installed"}``.

    Args:
        host: MCP server host.
        port: MCP server HTTP port.
        tool: Tool name.
        arguments: Tool arguments dict (optional).
        timeout: Request timeout in seconds.

    Returns:
        Parsed result dict, or ``{"error": "..."}`` on failure.
    """
    if not _AIOHTTP_AVAILABLE:
        return {"error": "aiohttp not installed; use mcp_call() for sync"}

    url = f"http://{host}:{port}/mcp/http"
    payload = _build_payload(tool, arguments)
    headers = {"Content-Type": "application/json"}
    timeout_obj = _imported_aiohttp.ClientTimeout(total=timeout)

    global _aiohttp_client
    if _aiohttp_client is None or _aiohttp_client.closed:
        _aiohttp_client = _imported_aiohttp.ClientSession(timeout=timeout_obj)

    try:
        async with _aiohttp_client.post(url, data=payload, headers=headers) as resp:
            raw = await resp.read()
            if resp.status != 200:
                logger.error(
                    "MCP HTTP error %d for %s", resp.status, tool
                )
                return {"error": f"HTTP {resp.status}"}
    except asyncio.TimeoutError:
        logger.error("MCP timeout for %s", tool)
        return {"error": f"Timeout after {timeout}s"}
    except _imported_aiohttp.ClientError as exc:
        logger.error("MCP aiohttp error for %s: %s", tool, exc)
        return {"error": f"Network error: {exc}"}
    except OSError as exc:
        logger.error("MCP OSError for %s: %s", tool, exc)
        return {"error": f"Network error: {exc}"}

    return _parse_response(raw, tool)


async def async_mcp_batch(
    host: str,
    port: int,
    calls: list[tuple[str, dict | None]],
    timeout: int = 30,
) -> list[dict]:
    """Execute multiple MCP calls concurrently (async).

    Args:
        host: MCP server host.
        port: MCP server HTTP port.
        calls: List of ``(tool, arguments)`` tuples.
        timeout: Request timeout per call.

    Returns:
        List of result dicts in same order as ``calls``.
    """
    tasks = [async_mcp_call(host, port, tool, args, timeout) for tool, args in calls]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    results: list[dict] = []
    for raw in raw_results:
        if isinstance(raw, Exception):
            results.append({"error": str(raw)})
        elif isinstance(raw, dict):
            results.append(raw)
        else:
            results.append({"error": f"Unexpected result type: {type(raw).__name__}"})
    return results


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


async def async_close() -> None:
    """Close the underlying aiohttp client session."""
    global _aiohttp_client
    if _aiohttp_client is not None and not _aiohttp_client.closed:
        await _aiohttp_client.close()


# ---------------------------------------------------------------------------
# Legacy port-reading helper
# ---------------------------------------------------------------------------


def read_port_from_config(config_path=None):
    """Read http_port from config.yaml (uses yaml library).

    Prefer the shared :func:`feyagate_skill.config.get_http_port`.
    """
    if config_path is None:
        return None
    try:
        import yaml as _yaml
        text = config_path.read_text(encoding="utf-8")
        data = _yaml.safe_load(text)
        if isinstance(data, dict):
            return int(data.get("server", {}).get("http_port", 38080))
    except Exception as exc:
        logger.warning("Failed to read port from %s: %s", config_path, exc)
    return None
