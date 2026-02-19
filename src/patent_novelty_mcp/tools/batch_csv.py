from __future__ import annotations

import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Sequence, Tuple

from patent_novelty_mcp.core.aggregator import aggregate_results
from patent_novelty_mcp.core.cache import JsonCache
from patent_novelty_mcp.core.models import ProviderResult
from patent_novelty_mcp.core.registry import ProviderRegistry


def _sniff_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8", errors="ignore")[:8192]
    sniffer = csv.Sniffer()
    try:
        return sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
    except Exception:
        return csv.get_dialect("excel")


def _read_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str], csv.Dialect]:
    dialect = _sniff_dialect(path)
    with path.open("r", encoding="utf-8", newline="") as fptr:
        reader = csv.DictReader(
            fptr,
            delimiter=getattr(dialect, "delimiter", ","),
            quotechar=getattr(dialect, "quotechar", '"'),
        )
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames, dialect


def _write_rows_atomic(path: Path, rows: Sequence[Dict[str, str]], fieldnames: Sequence[str], dialect: csv.Dialect) -> None:
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=str(path.parent),
        prefix=path.name,
        suffix=".tmp",
    ) as tmp:
        tmp_path = Path(tmp.name)
        writer = csv.DictWriter(
            tmp,
            fieldnames=list(fieldnames),
            delimiter=getattr(dialect, "delimiter", ","),
            quotechar=getattr(dialect, "quotechar", '"'),
            quoting=getattr(dialect, "quoting", csv.QUOTE_MINIMAL),
            lineterminator=getattr(dialect, "lineterminator", "\n"),
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, path)


def _find_query_column(fieldnames: Sequence[str], candidates: Sequence[str]) -> str | None:
    lowered = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def run(payload: Dict[str, Any], registry: ProviderRegistry, cache: JsonCache, creds: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    csv_paths = [Path(p).expanduser().resolve() for p in payload["csv_paths"]]
    providers = payload["providers"]
    query_candidates = payload.get(
        "query_column_candidates",
        ["SMILES", "smiles", "Scaffold", "canonical_smiles", "ligand_smiles", "InChIKey", "inchikey", "compound_name", "name"],
    )
    result_col = payload.get("result_column", "Result")
    aggregation_policy = payload.get("aggregation_policy", "any_hit_is_not_novel")
    query_type = payload.get("query_type", "smiles")
    max_new_queries = int(payload.get("max_new_queries", 0) or 0)

    # options fed to provider/cache key; only stable query options here.
    provider_options = payload.get("provider_options", {})

    file_state: Dict[Path, Tuple[List[Dict[str, str]], List[str], csv.Dialect, str]] = {}
    skipped_files: List[Dict[str, str]] = []

    unique_queries: List[str] = []
    seen_queries = set()

    for path in csv_paths:
        if not path.exists():
            skipped_files.append({"file": str(path), "reason": "file_not_found"})
            continue
        rows, fieldnames, dialect = _read_rows(path)
        query_col = _find_query_column(fieldnames, query_candidates)
        if not query_col:
            skipped_files.append({"file": str(path), "reason": "query_column_not_found"})
            continue

        file_state[path] = (rows, fieldnames, dialect, query_col)
        for row in rows:
            q = (row.get(query_col) or "").strip()
            if q and q not in seen_queries:
                seen_queries.add(q)
                unique_queries.append(q)

    # Prepare providers once.
    provider_instances = []
    for pname in providers:
        provider = registry.get(pname)
        provider.auth(creds.get(pname, {}))
        provider_instances.append((pname, provider))

    new_executed = 0
    cached_hits = 0
    provider_status_counts: Dict[str, int] = {}

    per_query_results: Dict[str, List[ProviderResult]] = {}

    for query in unique_queries:
        results_for_query: List[ProviderResult] = []
        for pname, provider in provider_instances:
            normalized = provider.normalize_query(query, query_type)
            key = JsonCache.make_key(pname, query_type, normalized, provider_options)
            cached = cache.get(key)
            if cached is not None:
                cached_hits += 1
                results_for_query.append(cached)
                provider_status_counts[cached.status] = provider_status_counts.get(cached.status, 0) + 1
                continue

            if max_new_queries and new_executed >= max_new_queries:
                unresolved = ProviderResult(
                    provider=pname,
                    status="unresolved",
                    hit=None,
                    result_count=None,
                    novelty_score=None,
                    confidence=None,
                    evidence={"reason": "max_new_queries_limit"},
                    error="Skipped due to max_new_queries limit",
                )
                results_for_query.append(unresolved)
                provider_status_counts[unresolved.status] = provider_status_counts.get(unresolved.status, 0) + 1
                continue

            provider.check_compliance(
                {
                    "query": query,
                    "query_type": query_type,
                    "providers": providers,
                    "options": provider_options,
                }
            )
            result = provider.query(normalized, query_type, provider_options)
            cache.put(key, result)
            new_executed += 1
            results_for_query.append(result)
            provider_status_counts[result.status] = provider_status_counts.get(result.status, 0) + 1

        per_query_results[query] = results_for_query

    # Apply aggregated novelty to files.
    files_updated = 0
    rows_processed = 0
    rows_written = 0
    unresolved_rows = 0

    for path, (rows, fieldnames, dialect, query_col) in file_state.items():
        final_fieldnames = list(fieldnames)
        if result_col not in final_fieldnames:
            final_fieldnames.append(result_col)

        for row in rows:
            rows_processed += 1
            q = (row.get(query_col) or "").strip()
            if not q:
                unresolved_rows += 1
                continue
            provider_results = per_query_results.get(q, [])
            aggregate = aggregate_results(provider_results, aggregation_policy)
            if aggregate.novelty_score is None:
                unresolved_rows += 1
                continue
            row[result_col] = str(int(aggregate.novelty_score))
            rows_written += 1

        _write_rows_atomic(path, rows, final_fieldnames, dialect)
        files_updated += 1

    return {
        "job_id": "sync-batch",
        "mode": "sync",
        "summary": {
            "files_updated": files_updated,
            "files_skipped": len(skipped_files),
            "rows_processed": rows_processed,
            "rows_written": rows_written,
            "rows_unresolved": unresolved_rows,
            "unique_queries": len(unique_queries),
            "cached_hits": cached_hits,
            "new_queries_executed": new_executed,
            "status_counts": provider_status_counts,
            "skipped_files": skipped_files,
        },
    }
