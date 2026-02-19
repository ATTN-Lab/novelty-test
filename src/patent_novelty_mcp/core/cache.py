from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .models import ProviderResult


class JsonCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, Any]] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    @staticmethod
    def make_key(provider: str, query_type: str, normalized_query: str, options: Dict[str, Any]) -> str:
        payload = json.dumps(
            {
                "provider": provider,
                "query_type": query_type,
                "query": normalized_query,
                "options": options,
            },
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[ProviderResult]:
        row = self._data.get(key)
        if not row:
            return None
        return ProviderResult(**row)

    def put(self, key: str, result: ProviderResult) -> None:
        self._data[key] = asdict(result)

    def flush(self) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
