#!/bin/bash
# WBGT熱中症警戒キオスク 統合ランチャー (Linux/macOS)
# WBGT Heat Stroke Warning Kiosk Unified Launcher (Linux/macOS)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 色付き出力関数
print_colored() {
    local color=$1
    local text=$2
    case $color in
        red) echo -e "\033[91m$text\033[0m" ;;
        green) echo -e "\033[92m$text\033[0m" ;;
        yellow) echo -e "\033[93m$text\033[0m" ;;
        blue) echo -e "\033[94m$text\033[0m" ;;
        cyan) echo -e "\033[96m$text\033[0m" ;;
        white) echo -e "\033[97m$text\033[0m" ;;
        *) echo "$text" ;;
    esac
}

# ヘルプ表示
show_help() {
    print_colored cyan "🌡️  WBGT熱中症警戒キオスク 統合ランチャー"
    print_colored cyan "🌡️  WBGT Heat Stroke Warning Kiosk Unified Launcher"
    echo "============================================================"
    echo
    print_colored white "使用方法 / Usage:"
    echo "  $0 [言語/language] [オプション/options]"
    echo
    print_colored yellow "言語選択 / Language Selection:"
    echo "  ja, jp, japanese    日本語版を起動 / Launch Japanese version"
    echo "  en, english         英語版を起動 / Launch English version"
    echo "  auto                システム言語を自動検出 / Auto-detect system language"
    echo
    print_colored yellow "オプション / Options:"
    echo "  --demo              デモモード / Demo mode"
    echo "  --gui               GUI版 / GUI version"
    echo "  --help, -h          このヘルプを表示 / Show this help"
    echo
    print_colored yellow "例 / Examples:"
    echo "  $0 ja --demo        日本語版デモモード / Japanese demo mode"
    echo "  $0 en --gui         英語版GUI / English GUI version"
    echo "  $0 auto             自動言語検出 / Auto language detection"
    echo
    print_colored green "仮想環境使用時 / With Virtual Environment:"
    echo "  事前にsetup_venv.batを実行してください"
    echo "  Run setup_venv.bat first if using virtual environment"
    echo "============================================================"
}

# システム言語検出
detect_language() {
    local lang="${LANG:-}"
    
    # 環境変数から言語を判定
    if [[ "$lang" =~ ^ja ]]; then
        echo "ja"
    elif [[ "$lang" =~ ^en ]]; then
        echo "en"
    else
        # デフォルトは英語
        echo "en"
    fi
}

# 仮想環境の確認とアクティベート
setup_virtual_env() {
    if [ -d "$SCRIPT_DIR/../venv" ]; then
        print_colored blue "📦 仮想環境をアクティベート中... / Activating virtual environment..."
        source "$SCRIPT_DIR/../venv/bin/activate"
        return 0
    else
        print_colored yellow "⚠️  仮想環境が見つかりません / Virtual environment not found"
        print_colored yellow "   システムのPythonを使用します / Using system Python"
        return 1
    fi
}

# メイン処理
main() {
    local language=""
    local options=()
    
    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            ja|jp|japanese)
                language="ja"
                shift
                ;;
            en|english)
                language="en"
                shift
                ;;
            auto)
                language="auto"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --demo|--gui)
                options+=("$1")
                shift
                ;;
            *)
                # 最初の未知の引数を言語として扱う
                if [ -z "$language" ]; then
                    case $1 in
                        *ja*|*jp*)
                            language="ja"
                            ;;
                        *en*)
                            language="en"
                            ;;
                        *)
                            print_colored red "❌ 不明なオプション / Unknown option: $1"
                            show_help
                            exit 1
                            ;;
                    esac
                else
                    print_colored red "❌ 不明なオプション / Unknown option: $1"
                    show_help
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # 言語が指定されていない場合は自動検出
    if [ -z "$language" ]; then
        language="auto"
    fi
    
    # auto の場合は実際の言語を検出
    if [ "$language" = "auto" ]; then
        language=$(detect_language)
        print_colored cyan "🔍 システム言語を検出 / Detected system language: $language"
    fi
    
    # 仮想環境のセットアップ
    setup_virtual_env
    
    # 言語に応じたアプリケーションを起動
    case $language in
        ja)
            print_colored green "🇯🇵 日本語版を起動 / Starting Japanese version..."
            if [ -f "$SCRIPT_DIR/../src/wbgt_kiosk.py" ]; then
                python "$SCRIPT_DIR/../src/wbgt_kiosk.py" "${options[@]}"
            else
                print_colored red "❌ 日本語版が見つかりません / Japanese version not found: src/wbgt_kiosk.py"
                exit 1
            fi
            ;;
        en)
            print_colored green "🇺🇸 英語版を起動 / Starting English version..."
            if [ -f "$SCRIPT_DIR/../src/wbgt_kiosk_en.py" ]; then
                python "$SCRIPT_DIR/../src/wbgt_kiosk_en.py" "${options[@]}"
            else
                print_colored red "❌ 英語版が見つかりません / English version not found: src/wbgt_kiosk_en.py"
                exit 1
            fi
            ;;
        *)
            print_colored red "❌ サポートされていない言語 / Unsupported language: $language"
            show_help
            exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"