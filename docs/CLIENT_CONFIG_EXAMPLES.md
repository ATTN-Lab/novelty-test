# MCP Client Config Examples

See also: `docs/CLIENT_SETUP.md` for complete end-to-end setup.

## Generic stdio server command
```bash
/absolute/path/to/novelty-test/run_stdio.sh
```

## Codex-style MCP config (example)
```json
{
  "mcpServers": {
    "patent-novelty": {
      "command": "/absolute/path/to/novelty-test/run_stdio.sh",
      "env": {
        "WIPO_USERNAME": "${WIPO_USERNAME}",
        "WIPO_PASSWORD": "${WIPO_PASSWORD}"
      }
    }
  }
}
```

## Claude Desktop-style MCP config (example)
```json
{
  "mcpServers": {
    "patent-novelty": {
      "command": "/absolute/path/to/novelty-test/run_stdio.sh",
      "args": [],
      "env": {
        "WIPO_USERNAME": "${WIPO_USERNAME}",
        "WIPO_PASSWORD": "${WIPO_PASSWORD}"
      }
    }
  }
}
```

Adjust to your actual client config format if field names differ.

## Streamable HTTP endpoint (if client supports URL-based MCP)
Start server with:
```bash
./run_http.sh
```

Endpoint:
```text
http://localhost:8000/mcp
```

## Ready-to-copy templates
- `docs/client-config/claude_desktop.stdio.json`
- `docs/client-config/codex.stdio.json`
- `docs/client-config/http.url.json`
