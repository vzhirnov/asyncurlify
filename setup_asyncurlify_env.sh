#!/usr/bin/env bash
# -------------------------------------------------------------
# Creates virtual environment `asyncurlify-venv` and installs:
#   • **runtime dependencies** of the library (aiohttp for type-checking)
#   • **dev dependencies** for running tests
# -------------------------------------------------------------
set -Eeuo pipefail

VENV_NAME="asyncurlify-venv"          # same name as the package
PYTHON=${PYTHON:=python3}      # can be overridden: PYTHON=python3.12 ./script.sh

# 1. Create and activate venv
$PYTHON -m venv "$VENV_NAME"
# shellcheck source=/dev/null
source "$VENV_NAME/bin/activate"

# 2. Update base tools
python -m pip install --upgrade pip setuptools wheel

# 3. Runtime dependencies (the lib only needs aiohttp for type-checking)
python -m pip install "aiohttp>=3.9"

# 4. Development and testing tools
python -m pip install \
    "pytest>=8.2" \
    "pytest-cov>=5.0"

# 5. Install the package itself in development mode
pip install -e .

echo
echo "✅  Done!  Activate the environment with:"
echo "   source $VENV_NAME/bin/activate"
