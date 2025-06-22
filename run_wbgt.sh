#!/bin/bash
# WBGT キオスク実行スクリプト（仮想環境用）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 仮想環境をアクティベート
source "$SCRIPT_DIR/venv/bin/activate"

# アプリケーションを実行
python "$SCRIPT_DIR/wbgt_kiosk.py" "$@"
