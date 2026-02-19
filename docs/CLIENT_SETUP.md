# MCP Client Setup (Claude + Codex)

This guide shows how to wire `patent-novelty-mcp` into real MCP clients.

## Prerequisites
- Python `3.10+` (`3.11` recommended)
- WIPO credentials
- Repo cloned locally

```bash
git clone https://github.com/ATTN-Lab/novelty-test.git
cd novelty-test
```

## Option A: Stdio transport (recommended)
Use this for Claude Desktop and Codex MCP integrations.

Set credentials:
```bash
export WIPO_USERNAME='your_wipo_username'
export WIPO_PASSWORD='your_wipo_password'
```

If your default `python3` is older than 3.10, set interpreter explicitly:
```bash
export PYTHON_BIN='/absolute/path/to/python3.11'
```

Server command:
```bash
/absolute/path/to/novelty-test/run_stdio.sh
```

## Option B: Streamable HTTP transport
Start server:
```bash
cd /absolute/path/to/novelty-test
MCP_PORT=8010 ./run_http.sh
```

Endpoint:
```text
http://localhost:8010/mcp
```

## Client Config Templates
- Claude Desktop stdio template:
  - `docs/client-config/claude_desktop.stdio.json`
- Codex stdio template:
  - `docs/client-config/codex.stdio.json`
- URL-based MCP template:
  - `docs/client-config/http.url.json`

## Smoke Test
After connecting client to this MCP server:
1. Call `novelty.providers.list`
2. Call `novelty.query` with:
   - `query_type`: `compound_name`
   - `query`: `ibuprofen`
   - `providers`: `["wipo_patentscope"]`

If these return successfully, the integration is ready for `novelty.batch_csv`.
