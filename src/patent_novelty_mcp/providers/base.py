from __future__ import annotations

from typing import Any, Dict

from patent_novelty_mcp.core.models import ProviderResult


class BaseProvider:
    name = "base"

    def capabilities(self) -> Dict[str, Any]:
        raise NotImplementedError

    def auth(self, creds: Dict[str, Any]) -> None:
        raise NotImplementedError

    def check_compliance(self, request: Dict[str, Any]) -> None:
        raise NotImplementedError

    def normalize_query(self, query: str, query_type: str) -> str:
        return query.strip()

    def query(self, query: str, query_type: str, options: Dict[str, Any]) -> ProviderResult:
        raise NotImplementedError

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "provider": self.name}
