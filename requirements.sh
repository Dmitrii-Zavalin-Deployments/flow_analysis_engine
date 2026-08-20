#!/usr/bin/env bash
set -euo pipefail

echo "📦 Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Environment provisioning completed successfully."
