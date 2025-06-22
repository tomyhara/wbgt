#!/bin/bash
# WBGT熱中症警戒キオスク 自動起動スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
LOG_FILE="$SCRIPT_DIR/autostart.log"

# ログファイルに開始メッセージ
echo "$(date): 🌡️ WBGT熱中症警戒キオスク 自動起動開始" >> "$LOG_FILE"

# ディスプレイ環境変数を設定（GUI版使用時）
export DISPLAY=:0.0

# 作業ディレクトリに移動
cd "$SCRIPT_DIR"

# 設定ファイルの存在確認
if [ ! -f "config.py" ]; then
    echo "$(date): ❌ エラー - config.py が見つかりません" >> "$LOG_FILE"
    echo "$(date): config.sample.py をコピーして config.py を作成してください" >> "$LOG_FILE"
    exit 1
fi

# ネットワーク接続待機
echo "$(date): 🌐 ネットワーク接続を待機中..." >> "$LOG_FILE"
sleep 15

# Python環境の確認
if ! command -v python3 &> /dev/null; then
    echo "$(date): ❌ Python3が見つかりません" >> "$LOG_FILE"
    exit 1
fi

# 依存関係の確認
if ! python3 -c "import requests" &> /dev/null; then
    echo "$(date): ⚠️ 依存関係をインストール中..." >> "$LOG_FILE"
    pip3 install -r requirements.txt >> "$LOG_FILE" 2>&1
fi

# アプリケーション開始
echo "$(date): 🚀 WBGTキオスクアプリケーション開始" >> "$LOG_FILE"

# 通常モードで起動（GUI版を使いたい場合は --gui を追加）
python3 wbgt_kiosk.py >> "$LOG_FILE" 2>&1

# 終了ログ
echo "$(date): 🛑 WBGTキオスクアプリケーション終了" >> "$LOG_FILE"