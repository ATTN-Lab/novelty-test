#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY311="/Users/tim/opt/anaconda3/envs/bbbnuke/bin/python"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

# Optional credentials for live WIPO provider usage:
# export WIPO_USERNAME='...'
# export WIPO_PASSWORD='...'

exec "$PY311" -m patent_novelty_mcp
