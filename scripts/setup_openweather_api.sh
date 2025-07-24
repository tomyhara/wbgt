#!/bin/bash
# OpenWeatherMap API Key Setup Script
# OpenWeatherMap APIキー設定スクリプト

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
PROJECT_ROOT="$(get_project_root)"
CONFIG_FILE="$PROJECT_ROOT/setup/config.json"

show_header "OpenWeatherMap APIキー設定 / OpenWeatherMap API Key Setup"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    print_colored red "❌ 設定ファイルが見つかりません / Configuration file not found: $CONFIG_FILE"
    cleanup_and_exit 1
fi

# Current API key status
current_key=$(python3 -c "
import sys, os, json
sys.path.append('$PROJECT_ROOT/setup')
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    key = config.get('openweather_api_key', '')
    if key == 'YOUR_OPENWEATHERMAP_API_KEY_HERE' or not key:
        print('not_set')
    else:
        print('set')
        print(key[:8] + '...' + key[-4:] if len(key) > 12 else key)
except:
    print('error')
" 2>/dev/null)

if [[ "$current_key" == "set"* ]]; then
    masked_key=$(echo "$current_key" | tail -n 1)
    print_colored green "✅ APIキーが設定済みです / API key is already set: $masked_key"
    echo
    read -p "新しいAPIキーで上書きしますか？ / Overwrite with new API key? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_colored cyan "設定をキャンセルしました / Setup cancelled"
        exit 0
    fi
elif [ "$current_key" = "not_set" ]; then
    print_colored yellow "⚠️  APIキーが設定されていません / API key not set"
else
    print_colored red "❌ 設定ファイルの読み込みに失敗しました / Failed to read configuration file"
    cleanup_and_exit 1
fi

echo
print_colored cyan "📋 OpenWeatherMap APIキー取得手順 / How to get OpenWeatherMap API Key:"
echo "1. https://openweathermap.org/api にアクセス"
echo "2. アカウントを作成（無料） / Create account (free)"
echo "3. API Keys ページでキーを取得 / Get key from API Keys page"
echo "4. 無料プランで1,000 calls/day利用可能 / Free plan: 1,000 calls/day"
echo

# Prompt for API key
read -p "OpenWeatherMap APIキーを入力してください / Enter OpenWeatherMap API key: " api_key

# Validate input
if [ -z "$api_key" ]; then
    print_colored red "❌ APIキーが入力されていません / API key not provided"
    cleanup_and_exit 1
fi

if [ ${#api_key} -lt 16 ]; then
    print_colored yellow "⚠️  APIキーが短すぎるようです（通常32文字）/ API key seems too short (usually 32 chars)"
    read -p "続行しますか？ / Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        cleanup_and_exit 1
    fi
fi

# Update configuration file
print_colored cyan "📝 設定ファイルを更新中... / Updating configuration file..."

# Create backup
cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

# Update JSON file
python3 -c "
import json
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    
    config['openweather_api_key'] = '$api_key'
    
    with open('$CONFIG_FILE', 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print('success')
except Exception as e:
    print(f'error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_colored green "✅ APIキーが正常に設定されました / API key set successfully"
    
    # Test API key
    print_colored cyan "🧪 APIキーをテスト中... / Testing API key..."
    
    test_result=$(curl -s --connect-timeout 10 --max-time 10 \
        "https://api.openweathermap.org/data/2.5/weather?q=Tokyo,JP&appid=$api_key&units=metric" \
        | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'main' in data and 'temp' in data['main']:
        print('success')
        print(f'Temperature in Tokyo: {data[\"main\"][\"temp\"]}°C')
    elif 'cod' in data and data['cod'] == 401:
        print('invalid_key')
    else:
        print('error')
        print(f'Response: {data}')
except:
    print('network_error')
" 2>/dev/null)
    
    if [[ "$test_result" == "success"* ]]; then
        temp_info=$(echo "$test_result" | tail -n 1)
        print_colored green "🎉 APIキーのテストが成功しました！ / API key test successful!"
        print_colored green "   $temp_info"
    elif [ "$test_result" = "invalid_key" ]; then
        print_colored red "❌ APIキーが無効です / Invalid API key"
        print_colored yellow "   OpenWeatherMapで正しいキーを確認してください / Please verify the key in OpenWeatherMap"
    elif [ "$test_result" = "network_error" ]; then
        print_colored yellow "⚠️  ネットワークエラー（キーは設定済み）/ Network error (key is configured)"
        print_colored yellow "   後でテストしてください / Please test later"
    else
        print_colored yellow "⚠️  テストでエラーが発生しましたが、キーは設定済みです / Test error, but key is configured"
    fi
    
    echo
    print_colored cyan "📱 次のステップ / Next steps:"
    echo "1. アプリケーションを再起動 / Restart application"
    echo "2. オフラインデータをダウンロード（オプション）/ Download offline data (optional):"
    echo "   ./scripts/download_openweather_data.sh"
    echo "3. 動作確認 / Test functionality:"
    echo "   python3 test_openweather_offline.py"
    
else
    print_colored red "❌ 設定ファイルの更新に失敗しました / Failed to update configuration file"
    cleanup_and_exit 1
fi