from __future__ import annotations

from typing import List

from .models import ProviderResult, QueryAggregate


def aggregate_results(results: List[ProviderResult], policy: str = "any_hit_is_not_novel") -> QueryAggregate:
    ok_results = [r for r in results if r.status == "ok" and r.hit is not None]
    if not ok_results:
        return QueryAggregate(policy=policy, hit_any=None, novelty_score=None)

    if policy == "any_hit_is_not_novel":
        hit_any = any(bool(r.hit) for r in ok_results)
        return QueryAggregate(policy=policy, hit_any=hit_any, novelty_score=0 if hit_any else 1)

    # Placeholder until additional policies are implemented.
    hit_any = any(bool(r.hit) for r in ok_results)
    return QueryAggregate(policy=policy, hit_any=hit_any, novelty_score=0 if hit_any else 1)
