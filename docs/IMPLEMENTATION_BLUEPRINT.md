# Patent Novelty MCP: Implementation Blueprint

## Goal
Build an MCP server that exposes a normalized novelty-check workflow across patent providers:
- `wipo_patentscope`
- `google_patents`
- `epo_espacenet`

## Tool Surface (v0.1)
- `novelty.providers.list`
- `novelty.query`
- `novelty.batch_csv`
- `novelty.cache.get`
- `novelty.cache.put`
- `novelty.job.status`
- `novelty.job.cancel`

## Architecture
1. MCP transport layer (`server.py`)
2. Tool handlers (`tools/*.py`)
3. Core services:
- provider registry
- aggregator
- cache backend
- job manager
4. Provider plugins (`providers/*.py`)

## Phased Build Plan
1. Foundations
- Implement models, provider interface, registry, cache abstraction
- Add schema validation and shared error contract

2. WIPO provider (first production provider)
- Auth/session
- SMILES query workflow
- Parse result count and normalize output
- Add provider-specific throttling/backoff

3. Tool endpoints
- `providers.list`, `query`, `batch_csv` first
- Then cache/job endpoints

4. Batch runner hardening
- Atomic CSV writes
- resume support
- per-row audit and status summaries

5. Additional providers
- add Google/EPO plugin skeletons
- use compliant paths only (official APIs where available)

## Runtime Contracts
- Canonical query key: `(provider, query_type, normalized_query, options_fingerprint)`
- Novelty mapping:
- `result_count > 0` => `novelty_score = 0`
- `result_count == 0` => `novelty_score = 1`
- unresolved => `novelty_score = null`

## Security + Ops
- Provider credentials via env vars or secret store
- Structured logs with request_id/job_id
- Audit trail for provider query outcomes
- Never implement anti-bot bypass techniques

## Suggested Next Steps
1. Implement MCP server entrypoint and tool registration
2. Complete WIPO plugin with integration tests
3. Add SQLite cache backend
4. Add end-to-end batch CSV test fixture
