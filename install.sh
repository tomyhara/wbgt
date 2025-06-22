#!/bin/bash

echo "🌡️  WBGT熱中症警戒キオスク セットアップ  🌡️"
echo "=============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 色付き出力のための関数
print_success() {
    echo -e "\033[92m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[96mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[93m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[91m❌ $1\033[0m"
}

# Pythonバージョンチェック
print_info "Pythonバージョンを確認中..."
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "Python確認: $python_version"
else
    print_error "Python3が見つかりません。Python3をインストールしてください。"
    exit 1
fi

# 依存関係のインストール
print_info "Pythonの依存関係をインストール中..."
if pip3 install -r "$SCRIPT_DIR/requirements.txt"; then
    print_success "依存関係のインストール完了"
else
    print_warning "依存関係のインストールで問題が発生しました"
fi

# 設定ファイルの作成
print_info "設定ファイルを確認中..."
if [ ! -f "$SCRIPT_DIR/config.py" ]; then
    cp "$SCRIPT_DIR/config.sample.py" "$SCRIPT_DIR/config.py"
    print_success "config.py を作成しました"
    print_info "デフォルト設定（東京）で動作します"
else
    print_info "config.py は既に存在します"
fi

# スクリプトを実行可能にする
print_info "スクリプトファイルを実行可能にする..."
chmod +x "$SCRIPT_DIR/wbgt_kiosk.py"
chmod +x "$SCRIPT_DIR/autostart.sh"
print_success "実行権限を設定しました"

# 動作テスト
print_info "動作テストを実行中..."
if python3 "$SCRIPT_DIR/wbgt_kiosk.py" --demo > /dev/null 2>&1; then
    print_success "動作テスト成功"
else
    print_warning "動作テストで問題が発生しましたが、継続します"
fi

echo ""
echo "=============================================="
print_success "🎉 セットアップ完了！"
echo ""
echo "📱 使用方法："
echo "  デモモード:     python3 wbgt_kiosk.py --demo"
echo "  通常モード:     python3 wbgt_kiosk.py"
echo "  GUI版（実験的）: python3 wbgt_kiosk.py --gui"
echo ""
echo "🗾 地域設定："
echo "  地域を変更する場合は config.py を編集してください"
echo "  例：nano config.py"
echo ""
echo "🔧 自動起動設定："
echo "  systemd使用（推奨）:"
echo "    sudo cp wbgt-kiosk.service /etc/systemd/system/"
echo "    sudo systemctl enable wbgt-kiosk.service"
echo ""
echo "  crontab使用:"
echo "    crontab -e"
echo "    @reboot cd $SCRIPT_DIR && python3 wbgt_kiosk.py"
echo ""
print_info "まずはデモモードで動作確認してみてください："
echo "python3 wbgt_kiosk.py --demo"
echo "=============================================="