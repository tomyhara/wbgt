#!/bin/bash
# WBGT Heat Stroke Warning Kiosk Execution Script (English Version) - Virtual Environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Activate virtual environment
source "$SCRIPT_DIR/../venv/bin/activate"

# Run application
python "$SCRIPT_DIR/../src/wbgt_kiosk_en.py" "$@"