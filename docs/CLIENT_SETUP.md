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

## Minimal Workflow (Compressed)
1. Configure secrets once:
```bash
cp .env.example .env
# edit .env with WIPO_USERNAME / WIPO_PASSWORD
```

2. Start MCP (stdio for Codex/Claude):
```bash
scripts/novelty mcp
```

3. Optional HTTP mode:
```bash
scripts/novelty http 8010
```

## Client Config Templates
- Claude Desktop stdio template:
  - `docs/client-config/claude_desktop.stdio.json`
- Codex stdio template:
  - `docs/client-config/codex.stdio.json`
- URL-based MCP template:
  - `docs/client-config/http.url.json`

## Smoke Test
Without writing JSON manually:
```bash
scripts/novelty smoke
scripts/novelty query compound_name ibuprofen
```

If these return successfully, the integration is ready for `novelty.batch_csv`.
