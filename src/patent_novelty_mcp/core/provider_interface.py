from __future__ import annotations

from typing import Any, Dict, Protocol

from .models import ProviderResult


class ProviderPlugin(Protocol):
    name: str

    def capabilities(self) -> Dict[str, Any]:
        ...

    def auth(self, creds: Dict[str, Any]) -> None:
        ...

    def check_compliance(self, request: Dict[str, Any]) -> None:
        ...

    def normalize_query(self, query: str, query_type: str) -> str:
        ...

    def query(self, query: str, query_type: str, options: Dict[str, Any]) -> ProviderResult:
        ...

    def health(self) -> Dict[str, Any]:
        ...
