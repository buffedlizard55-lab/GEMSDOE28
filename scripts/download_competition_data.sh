#!/usr/bin/env bash
# Restore hash-pinned public owner mirrors; this script never contacts DrivenData.
set -euo pipefail
cd "$(dirname "$0")/.."
export GEMS_DATA_DIR="${GEMS_DATA_DIR:-$PWD/data}"
PY="${PYTHON:-python3}"
"$PY" scripts/restore_data.py --group all --data-dir "$GEMS_DATA_DIR"
"$PY" scripts/prepare_data.py --force
"$PY" scripts/verify_restored_inputs.py --data-dir "$GEMS_DATA_DIR" --manifest "$PWD/registry/data_manifest.json" --out "$PWD/evidence/restore_audit.json"
