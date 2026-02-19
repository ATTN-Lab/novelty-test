from __future__ import annotations

import uuid
import os
from pathlib import Path
from typing import Any, Dict

from jsonschema import validate
from mcp.server.fastmcp import FastMCP

from patent_novelty_mcp.core.cache import JsonCache
from patent_novelty_mcp.core.registry import ProviderRegistry
from patent_novelty_mcp.providers.wipo import WipoPatentscopeProvider
from patent_novelty_mcp.tools.batch_csv import run as batch_csv_run
from patent_novelty_mcp.tools.novelty_query import run as novelty_query_run
from patent_novelty_mcp.tools.providers_list import run as providers_list_run


def _envelope_ok(request_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "ok": True,
        "data": data,
        "error": None,
    }


def _envelope_err(
    request_id: str,
    code: str,
    message: str,
    retryable: bool,
    provider: str | None = None,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "provider": provider,
            "retryable": retryable,
            "details": details or {},
        },
    }


class PatentNoveltyRuntime:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.schemas_dir = root_dir / "schemas"
        self.cache = JsonCache(root_dir / "runtime" / "novelty_cache.json")
        self.registry = ProviderRegistry()
        self.registry.register(WipoPatentscopeProvider())

    def schema(self, name: str) -> Dict[str, Any]:
        import json

        return json.loads((self.schemas_dir / name).read_text(encoding="utf-8"))


def build_server(root_dir: Path | None = None, host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    root = (root_dir or Path(__file__).resolve().parents[2]).resolve()
    runtime = PatentNoveltyRuntime(root)

    server = FastMCP(
        name="patent-novelty-mcp",
        instructions="Cross-provider patent novelty MCP server",
        host=host,
        port=port,
    )

    @server.tool(name="novelty.providers.list", description="List configured novelty providers and capabilities")
    def novelty_providers_list() -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        try:
            data = providers_list_run(runtime.registry)
            return _envelope_ok(request_id, data)
        except Exception as exc:  # pragma: no cover
            return _envelope_err(request_id, "INTERNAL_ERROR", str(exc), retryable=False)

    @server.tool(name="novelty.query", description="Run novelty query against one or more providers")
    def novelty_query(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        try:
            validate(payload, runtime.schema("novelty.query.request.schema.json"))
        except Exception as exc:
            return _envelope_err(
                request_id,
                "INVALID_INPUT",
                "Payload failed schema validation",
                retryable=False,
                details={"exception": str(exc)},
            )

        creds = {
            "wipo_patentscope": {
                "username": __import__("os").environ.get("WIPO_USERNAME", ""),
                "password": __import__("os").environ.get("WIPO_PASSWORD", ""),
            }
        }

        try:
            data = novelty_query_run(payload, runtime.registry, runtime.cache, creds)
            runtime.cache.flush()
            return _envelope_ok(request_id, data)
        except KeyError as exc:
            return _envelope_err(request_id, "INVALID_INPUT", str(exc), retryable=False)
        except ValueError as exc:
            return _envelope_err(request_id, "AUTH_FAILED", str(exc), retryable=False)
        except Exception as exc:  # pragma: no cover
            return _envelope_err(request_id, "INTERNAL_ERROR", str(exc), retryable=True)

    # Registered as stubs to match v0.1 surface.
    @server.tool(name="novelty.batch_csv", description="Batch novelty processing for CSV files (planned)")
    def novelty_batch_csv(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        try:
            validate(payload, runtime.schema("novelty.batch_csv.request.schema.json"))
        except Exception as exc:
            return _envelope_err(
                request_id,
                "INVALID_INPUT",
                "Payload failed schema validation",
                retryable=False,
                details={"exception": str(exc)},
            )
        creds = {
            "wipo_patentscope": {
                "username": __import__("os").environ.get("WIPO_USERNAME", ""),
                "password": __import__("os").environ.get("WIPO_PASSWORD", ""),
            }
        }
        try:
            data = batch_csv_run(payload, runtime.registry, runtime.cache, creds)
            runtime.cache.flush()
            return _envelope_ok(request_id, data)
        except KeyError as exc:
            return _envelope_err(request_id, "INVALID_INPUT", str(exc), retryable=False)
        except ValueError as exc:
            return _envelope_err(request_id, "AUTH_FAILED", str(exc), retryable=False)
        except Exception as exc:  # pragma: no cover
            return _envelope_err(request_id, "INTERNAL_ERROR", str(exc), retryable=True)

    @server.tool(name="novelty.cache.get", description="Get cached result by query/provider")
    def novelty_cache_get(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        try:
            provider = payload["provider"]
            query_type = payload["query_type"]
            query = payload["query"]
            options = payload.get("options", {})
            key = JsonCache.make_key(provider, query_type, query.strip(), options)
            hit = runtime.cache.get(key)
            return _envelope_ok(request_id, {"cache_key": key, "result": None if hit is None else hit.__dict__})
        except KeyError as exc:
            return _envelope_err(request_id, "INVALID_INPUT", f"missing field: {exc}", retryable=False)

    @server.tool(name="novelty.cache.put", description="Put provider result into cache")
    def novelty_cache_put(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        return _envelope_err(request_id, "NOT_IMPLEMENTED", "novelty.cache.put not implemented yet", retryable=False)

    @server.tool(name="novelty.job.status", description="Get async job status")
    def novelty_job_status(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        return _envelope_err(request_id, "NOT_IMPLEMENTED", "novelty.job.status not implemented yet", retryable=False)

    @server.tool(name="novelty.job.cancel", description="Cancel async job")
    def novelty_job_cancel(payload: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        return _envelope_err(request_id, "NOT_IMPLEMENTED", "novelty.job.cancel not implemented yet", retryable=False)

    return server


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    host = os.environ.get("MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(os.environ.get("MCP_PORT", "8000"))
    except ValueError:
        raise ValueError("MCP_PORT must be an integer")

    server = build_server(host=host, port=port)
    if transport == "sse":
        mount_path = os.environ.get("MCP_MOUNT_PATH", "/").strip() or "/"
        server.run(transport=transport, mount_path=mount_path)
        return
    server.run(transport=transport)


if __name__ == "__main__":
    main()
