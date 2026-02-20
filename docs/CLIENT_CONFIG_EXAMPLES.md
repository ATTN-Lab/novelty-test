# MCP Client Config Examples

See also: `docs/CLIENT_SETUP.md` for complete end-to-end setup.

## Generic stdio server command
```bash
/absolute/path/to/novelty-test/scripts/novelty mcp
```

## Codex-style MCP config (example)
```json
{
  "mcpServers": {
    "patent-novelty": {
      "command": "/absolute/path/to/novelty-test/scripts/novelty",
      "args": ["mcp"]
    }
  }
}
```

## Claude Desktop-style MCP config (example)
```json
{
  "mcpServers": {
    "patent-novelty": {
      "command": "/absolute/path/to/novelty-test/scripts/novelty",
      "args": ["mcp"]
    }
  }
}
```

Adjust to your actual client config format if field names differ.

## Streamable HTTP endpoint (if client supports URL-based MCP)
Start server with:
```bash
scripts/novelty http 8010
```

Endpoint:
```text
http://localhost:8000/mcp
```

## Ready-to-copy templates
- `docs/client-config/claude_desktop.stdio.json`
- `docs/client-config/codex.stdio.json`
- `docs/client-config/http.url.json`
