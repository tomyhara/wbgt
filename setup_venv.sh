#!/bin/bash

echo "🌡️  WBGT熱中症警戒キオスク 仮想環境セットアップ  🌡️"
echo "=================================================="

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

# 仮想環境の作成
print_info "Python仮想環境を作成中..."
if python3 -m venv "$SCRIPT_DIR/venv"; then
    print_success "仮想環境作成完了"
else
    print_error "仮想環境の作成に失敗しました"
    exit 1
fi

# 仮想環境をアクティベート
print_info "仮想環境をアクティベート中..."
source "$SCRIPT_DIR/venv/bin/activate"

# pipをアップグレード
print_info "pipをアップグレード中..."
pip install --upgrade pip

# 依存関係のインストール
print_info "依存関係をインストール中..."
if pip install -r "$SCRIPT_DIR/requirements.txt"; then
    print_success "依存関係のインストール完了"
else
    print_error "依存関係のインストールに失敗しました"
    exit 1
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

# 実行スクリプトの作成
print_info "実行スクリプトを作成中..."
cat > "$SCRIPT_DIR/run_wbgt.sh" << 'EOF'
#!/bin/bash
# WBGT キオスク実行スクリプト（仮想環境用）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 仮想環境をアクティベート
source "$SCRIPT_DIR/venv/bin/activate"

# アプリケーションを実行
python "$SCRIPT_DIR/wbgt_kiosk.py" "$@"
EOF

chmod +x "$SCRIPT_DIR/run_wbgt.sh"
print_success "実行スクリプト作成完了"

# 動作テスト
print_info "動作テストを実行中..."
if python "$SCRIPT_DIR/wbgt_kiosk.py" --demo > /dev/null 2>&1; then
    print_success "動作テスト成功"
else
    print_warning "動作テストで問題が発生しましたが、継続します"
fi

echo ""
echo "=================================================="
print_success "🎉 仮想環境セットアップ完了！"
echo ""
echo "📱 使用方法："
echo "  デモモード:     ./run_wbgt.sh --demo"
echo "  通常モード:     ./run_wbgt.sh"
echo "  GUI版（実験的）: ./run_wbgt.sh --gui"
echo ""
echo "🔧 手動実行の場合："
echo "  source venv/bin/activate"
echo "  python wbgt_kiosk.py --demo"
echo ""
echo "🗾 地域設定："
echo "  地域を変更する場合は config.py を編集してください"
echo ""
print_info "まずはデモモードで動作確認してみてください："
echo "./run_wbgt.sh --demo"
echo "=================================================="