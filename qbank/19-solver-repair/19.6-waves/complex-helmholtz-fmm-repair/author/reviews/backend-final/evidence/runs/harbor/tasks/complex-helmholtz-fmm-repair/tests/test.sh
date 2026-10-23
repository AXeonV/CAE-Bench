#!/bin/bash
set -euo pipefail
# Tests arrive only in the fresh verifier; the solver cannot read trusted data.
chmod 700 /tests /logs/verifier
python /tests/judge.py
