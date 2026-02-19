# patent-novelty-mcp (Blueprint)

This folder contains a pre-implementation blueprint for a cross-provider novelty MCP server.

## Contents
- `docs/IMPLEMENTATION_BLUEPRINT.md` : phased plan
- `schemas/*.json` : request/response schema drafts
- `src/patent_novelty_mcp/*` : module skeletons

## Current Status
- Contracts drafted
- Skeleton modules created
- MCP stdio transport wired with FastMCP
- Tool registration implemented for:
  - `novelty.providers.list`
  - `novelty.query`
  - `novelty.batch_csv` (stub)
  - `novelty.cache.get`
  - `novelty.cache.put` (stub)
  - `novelty.job.status` (stub)
  - `novelty.job.cancel` (stub)
- WIPO provider remains a stub until live client hookup
  - (Update) WIPO provider is now live for `novelty.query` / `novelty.batch_csv`

## Run (stdio)
```bash
cd /Users/tim/Desktop/ADHD/mcp/patent_novelty
./run_stdio.sh
```

Optional env vars for live WIPO calls once provider is implemented:
- `WIPO_USERNAME`
- `WIPO_PASSWORD`

## SSH Client Config Pattern
Use your MCP client config to launch:
- command: `/Users/tim/Desktop/ADHD/mcp/patent_novelty/run_stdio.sh`

This pattern is portable for Codex and Claude clients that support MCP stdio servers.

## Start Here
1. Implement async job manager tools (`novelty.job.status`, `novelty.job.cancel`)
2. Add Google/EPO provider plugins behind same interface

## Query Types
- Supported request `query_type`:
  - `smiles`
  - `inchi`
  - `inn`
  - `compound_name`

WIPO note:
- `inn` is accepted at API level, and currently routed through WIPO `COMPOUND` mode for runtime stability in headless automation.

## WIPO Defaults
- For WIPO chemical queries, defaults are now:
  - `scaffold_mode = false`
  - `include_markush_enumeration = false`
- Set these in `options` / `provider_options` only when explicitly needed.
