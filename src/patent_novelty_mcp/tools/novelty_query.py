from __future__ import annotations

from typing import Any, Dict, List

from patent_novelty_mcp.core.aggregator import aggregate_results
from patent_novelty_mcp.core.cache import JsonCache
from patent_novelty_mcp.core.models import ProviderResult
from patent_novelty_mcp.core.registry import ProviderRegistry


def run(payload: Dict[str, Any], registry: ProviderRegistry, cache: JsonCache, creds: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    query = payload["query"]
    query_type = payload["query_type"]
    options = payload.get("options", {})
    providers = payload["providers"]

    provider_results: List[ProviderResult] = []

    for pname in providers:
        provider = registry.get(pname)
        provider.auth(creds.get(pname, {}))
        provider.check_compliance(payload)
        normalized = provider.normalize_query(query, query_type)

        key = JsonCache.make_key(pname, query_type, normalized, options)
        cached = cache.get(key) if options.get("use_cache", True) and not options.get("force_refresh", False) else None

        result = cached or provider.query(normalized, query_type, options)
        if cached is None:
            cache.put(key, result)
        provider_results.append(result)

    aggregate = aggregate_results(provider_results, payload.get("aggregation_policy", "any_hit_is_not_novel"))
    return {
        "query": {
            "input": query,
            "query_type": query_type,
            "normalized_query": query,
        },
        "providers": [r.__dict__ for r in provider_results],
        "aggregate": aggregate.__dict__,
    }
