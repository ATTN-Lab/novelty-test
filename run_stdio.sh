#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON="${PYTHON_BIN}"
elif [[ -x "${VENV_DIR}/bin/python" ]]; then
  PYTHON="${VENV_DIR}/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m venv "${VENV_DIR}"
  PYTHON="${VENV_DIR}/bin/python"
else
  echo "No python3 interpreter found. Install Python 3.9+ and retry." >&2
  exit 1
fi

# Ensure runtime dependencies exist in the chosen interpreter.
if ! "${PYTHON}" - <<'PY' >/dev/null 2>&1
import importlib
for name in ("mcp.server.fastmcp", "jsonschema", "selenium"):
    importlib.import_module(name)
PY
then
  "${PYTHON}" -m pip install --upgrade pip >/dev/null
  "${PYTHON}" -m pip install -e "${ROOT_DIR}"
fi

exec "${PYTHON}" -m patent_novelty_mcp
