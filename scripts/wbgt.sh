#!/bin/bash
# WBGT熱中症警戒キオスク 統合ランチャー (Linux/macOS)
# WBGT Heat Stroke Warning Kiosk Unified Launcher (Linux/macOS)

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ヘルプ表示
show_help() {
    show_header "WBGT熱中症警戒キオスク 統合ランチャー / WBGT Heat Stroke Warning Kiosk Unified Launcher"
    
    print_colored white "使用方法 / Usage:"
    echo "  $0 [言語/language] [オプション/options]"
    echo
    print_colored yellow "言語選択 / Language Selection:"
    echo "  ja, jp, japanese    日本語版を起動 / Launch Japanese version"
    echo "  en, english         英語版を起動 / Launch English version"
    echo "  auto                システム言語を自動検出 / Auto-detect system language"
    echo
    print_colored yellow "オプション / Options:"
    echo "  --demo              デモモード (3回更新で終了) / Demo mode (3 updates then exit)"
    echo "  --gui               GUI版 (実験的) / GUI version (experimental)"
    echo "  --csv               CSVモード (オフライン) / CSV mode (offline)"
    echo "  --help, -h          このヘルプを表示 / Show this help"
    echo "  --version, -v       バージョン情報 / Version information"
    echo
    print_colored yellow "例 / Examples:"
    echo "  $0 ja --demo        日本語版デモモード / Japanese demo mode"
    echo "  $0 en --gui         英語版GUI / English GUI version"
    echo "  $0 auto --csv       自動言語検出・CSV / Auto detection with CSV mode"
    echo
    print_colored green "セットアップ / Setup:"
    echo "  仮想環境: ./setup/setup_venv.sh"
    echo "  設定: setup/config.json または setup/config.py"
    echo "  Virtual env: ./setup/setup_venv.sh"
    echo "  Config: setup/config.json or setup/config.py"
}

# バージョン情報表示
show_version() {
    show_header "WBGT熱中症警戒キオスク / WBGT Heat Stroke Warning Kiosk"
    print_colored green "Version: 2.0.0"
    print_colored cyan "Release Date: July 2025"
    echo
    print_colored white "新機能 / New Features:"
    echo "  • JSON設定ファイル対応 / JSON configuration support"
    echo "  • 複数地点監視 / Multi-location monitoring"
    echo "  • CSVモード改善 / Enhanced CSV mode"
    echo "  • 設定連携機能 / Configuration integration"
    echo
    print_colored white "データソース / Data Sources:"
    echo "  • 環境省熱中症予防情報サイト / Ministry of Environment WBGT Service"
    echo "  • 気象庁API / Japan Meteorological Agency API"
}

# メイン処理
main() {
    local language=""
    local options=()
    local csv_mode=false
    
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
                cleanup_and_exit 0
                ;;
            --version|-v)
                show_version
                cleanup_and_exit 0
                ;;
            --demo|--gui)
                options+=("$1")
                shift
                ;;
            --csv)
                csv_mode=true
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
                            log_message "Unknown option: $1" "ERROR"
                            show_help
                            cleanup_and_exit 1
                            ;;
                    esac
                else
                    log_message "Unknown option: $1" "ERROR"
                    show_help
                    cleanup_and_exit 1
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
        language=$(detect_system_language)
        log_message "Detected system language: $language" "INFO"
    fi
    
    # Python環境チェック
    if ! check_python; then
        cleanup_and_exit 1 "Python environment check failed"
    fi
    
    # 仮想環境のセットアップ
    setup_virtual_env
    
    # CSVモードの場合
    if [ "$csv_mode" = true ]; then
        log_message "Running in CSV mode" "INFO"
        export FORCE_CSV_MODE=1
        if [ "$language" = "en" ]; then
            exec "$SCRIPT_DIR/run_with_csv.sh" --english "${options[@]}"
        else
            exec "$SCRIPT_DIR/run_with_csv.sh" "${options[@]}"
        fi
    fi
    
    # 通常モード - 言語に応じたアプリケーションを起動
    local project_root="$(get_project_root)"
    case $language in
        ja)
            log_message "Starting Japanese version..." "INFO"
            local app_path="$project_root/src/wbgt_kiosk.py"
            if check_file "$app_path" "Japanese application"; then
                python3 "$app_path" "${options[@]}"
                local exit_code=$?
                cleanup_and_exit $exit_code "Japanese version completed with exit code: $exit_code"
            else
                cleanup_and_exit 1 "Japanese version not found"
            fi
            ;;
        en)
            log_message "Starting English version..." "INFO"
            local app_path="$project_root/src/wbgt_kiosk_en.py"
            if check_file "$app_path" "English application"; then
                python3 "$app_path" "${options[@]}"
                local exit_code=$?
                cleanup_and_exit $exit_code "English version completed with exit code: $exit_code"
            else
                cleanup_and_exit 1 "English version not found"
            fi
            ;;
        *)
            log_message "Unsupported language: $language" "ERROR"
            show_help
            cleanup_and_exit 1
            ;;
    esac
}

# スクリプト実行
main "$@"