#!/usr/bin/env bash
# -------------------------------------------------------------
# Создаёт одноимённое виртуальное окружение `uncurlify`
# и ставит:
#   • **runtime-зависимости** библиотеки (aiohttp — для типизации)
#   • **dev-зависимости** для запуска тестов
# -------------------------------------------------------------
set -Eeuo pipefail

VENV_NAME="uncurlify"          # «одноимённый» = такое же имя, как у пакета
PYTHON=${PYTHON:=python3}      # можно переопределить: PYTHON=python3.12 ./script.sh

# 1. Создание и активация venv
$PYTHON -m venv "$VENV_NAME"
# shellcheck source=/dev/null
source "$VENV_NAME/bin/activate"

# 2. Обновление базовых инструментов
python -m pip install --upgrade pip setuptools wheel

# 3. Runtime-зависимости (самой lib нужен только aiohttp для type-checking)
python -m pip install "aiohttp>=3.9"

# 4. Инструменты разработки и тестирования
python -m pip install \
    "pytest>=8.2" \
    "pytest-cov>=5.0"

# ③ ставим сам пакет в режиме разработки
pip install -e .

echo
echo "✅  Готово!  Активируйте окружение командой:"
echo "   source $VENV_NAME/bin/activate"
