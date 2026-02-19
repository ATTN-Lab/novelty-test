# patent-novelty-mcp

Cross-provider novelty MCP server with a live WIPO provider and an extensible provider interface.

## Contents
- `docs/IMPLEMENTATION_BLUEPRINT.md` : phased plan
- `schemas/*.json` : request/response schema drafts
- `src/patent_novelty_mcp/*` : module skeletons

## Current Status
- MCP stdio transport wired with FastMCP
- Tool registration implemented for:
  - `novelty.providers.list`
  - `novelty.query`
  - `novelty.batch_csv`
  - `novelty.cache.get`
  - `novelty.cache.put` (stub)
  - `novelty.job.status` (stub)
  - `novelty.job.cancel` (stub)
- WIPO provider is live for `novelty.query` / `novelty.batch_csv`

## Quick Start (Universal)
```bash
git clone git@github.com:ATTN-Lab/novelty-test.git
cd novelty-test

# Required for live WIPO calls:
export WIPO_USERNAME='...'
export WIPO_PASSWORD='...'

# run_stdio.sh now auto-creates .venv and installs dependencies as needed
./run_stdio.sh
```

Notes:
- Override interpreter if needed: `PYTHON_BIN=/path/to/python ./run_stdio.sh`
- First startup can take longer due to dependency installation.

## HTTP Mode
Run as a local HTTP MCP server (default `0.0.0.0:8000`):
```bash
cd novelty-test
export WIPO_USERNAME='...'
export WIPO_PASSWORD='...'
./run_http.sh
```

Optional overrides:
- `MCP_HOST` (default `0.0.0.0` in `run_http.sh`)
- `MCP_PORT` (default `8000`)
- `MCP_TRANSPORT` (`stdio`, `sse`, or `streamable-http`)

## Docker
```bash
cd novelty-test
docker build -t patent-novelty-mcp .
docker run --rm -p 8000:8000 \
  -e WIPO_USERNAME='...' \
  -e WIPO_PASSWORD='...' \
  patent-novelty-mcp
```
This starts Streamable HTTP MCP on `http://localhost:8000/mcp`.

## SSH Client Config Pattern
Use your MCP client config to launch:
- command: `/absolute/path/to/novelty-test/run_stdio.sh`

This pattern is portable for Codex and Claude clients that support MCP stdio servers.
Detailed setup and templates:
- `docs/CLIENT_SETUP.md`
- `docs/client-config/*.json`

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
