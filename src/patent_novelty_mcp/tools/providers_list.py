from __future__ import annotations

from typing import Any, Dict

from patent_novelty_mcp.core.registry import ProviderRegistry


def run(registry: ProviderRegistry) -> Dict[str, Any]:
    providers = []
    for name, provider in registry.list().items():
        providers.append(
            {
                "name": name,
                "supports": provider.capabilities(),
                "auth_required": bool(provider.capabilities().get("auth_required", False)),
            }
        )
    return {"providers": providers}
