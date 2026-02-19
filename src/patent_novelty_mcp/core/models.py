from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProviderResult:
    provider: str
    status: str
    hit: Optional[bool]
    result_count: Optional[int]
    novelty_score: Optional[int]
    confidence: Optional[float]
    evidence: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class QueryAggregate:
    policy: str
    hit_any: Optional[bool]
    novelty_score: Optional[int]


@dataclass
class QueryResponseData:
    query: Dict[str, Any]
    providers: List[ProviderResult]
    aggregate: QueryAggregate


@dataclass
class ErrorBody:
    code: str
    message: str
    provider: Optional[str]
    retryable: bool
    details: Dict[str, Any] = field(default_factory=dict)
