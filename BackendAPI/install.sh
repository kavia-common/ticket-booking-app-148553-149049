#!/usr/bin/env bash
# Simple bootstrap installer for BackendAPI
# - Installs Python dependencies from requirements.txt into the active environment.
# - Non-interactive and idempotent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ_FILE="${SCRIPT_DIR}/requirements.txt"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found on PATH." >&2
  exit 1
fi

PY="${PYTHON:-python3}"
PIP="${PIP:-${PY} -m pip}"

# Upgrade pip tooling (safe)
${PIP} install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
${PIP} install -r "${REQ_FILE}"

echo "Dependencies installed successfully."
