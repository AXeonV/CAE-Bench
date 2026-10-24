#!/bin/bash
set -euo pipefail
# Tests arrive only in the fresh verifier; the solver cannot read trusted data.
chmod 700 /tests /logs/verifier
if [ ! -f /tests/source-repair.json ]; then
    python /tests/check_environment.py
fi
python /tests/judge.py
