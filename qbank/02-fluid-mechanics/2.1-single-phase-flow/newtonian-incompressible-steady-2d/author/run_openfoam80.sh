#!/usr/bin/env bash
if [ -n "${MPI_BIN:-}" ]; then export PATH="$MPI_BIN:$PATH"; fi
source "${OPENFOAM_BASHRC:?Set OPENFOAM_BASHRC to the pinned producer etc/bashrc}"
set -eo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
exec "${PYTHON:-python3}" "$(dirname "$0")/crosscheck_openfoam.py" "$@"
