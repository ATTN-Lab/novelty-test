from __future__ import annotations

from typing import Dict

from .provider_interface import ProviderPlugin


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ProviderPlugin] = {}

    def register(self, provider: ProviderPlugin) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> ProviderPlugin:
        if name not in self._providers:
            raise KeyError(f"Provider not registered: {name}")
        return self._providers[name]

    def list(self) -> Dict[str, ProviderPlugin]:
        return dict(self._providers)
