#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Nocturnix AI Assistant environment setup"
echo "========================================"

echo
echo "Working directory:"
pwd

echo
echo "Git version:"
git --version

echo
echo "Python version:"
python --version

echo
echo "Creating virtual environment..."

if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

source .venv/bin/activate

echo
echo "Upgrading Python packaging tools..."
python -m pip install --upgrade pip setuptools wheel

echo
echo "Installing project dependencies..."

if [ -f "pyproject.toml" ]; then
    python -m pip install -e ".[dev]" || python -m pip install -e .
elif [ -f "requirements-dev.txt" ]; then
    python -m pip install -r requirements-dev.txt
elif [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
else
    echo "No dependency file was found."
    echo "Skipping dependency installation."
fi

echo
echo "Installed Python packages:"
python -m pip list

echo
echo "Environment setup complete."
