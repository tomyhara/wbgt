#!/bin/bash
# WBGT キオスク実行スクリプト（英語版）
# WBGT Kiosk Runner Script (English Version)

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Show help function
show_help() {
    show_header "WBGT Heat Stroke Warning Kiosk (English) / WBGT熱中症警戒キオスク（英語版）"
    
    print_colored white "Usage / 使用方法:"
    echo "  $0 [OPTIONS]"
    echo
    print_colored yellow "Options / オプション:"
    echo "  --demo              Demo mode (3 updates then exit) / デモモード (3回更新で終了)"
    echo "  --gui               GUI version (experimental) / GUI版 (実験的)"
    echo "  --help, -h          Show this help / ヘルプ表示"
    echo "  --version, -v       Version information / バージョン情報"
    echo
    print_colored yellow "Examples / 例:"
    echo "  $0                  Normal mode / 通常モード"
    echo "  $0 --demo          Demo mode / デモモード"
    echo "  $0 --gui           GUI version / GUI版"
    echo
    print_colored green "Configuration / 設定:"
    echo "  Config file: setup/config.json or setup/config.py"
    echo "  設定ファイル: setup/config.json または setup/config.py"
}

# Show version
show_version() {
    show_header "WBGT Heat Stroke Warning Kiosk (English)"
    print_colored green "Version: 2.0.0"
    print_colored cyan "Language: English"
}

# Main function
main() {
    local project_root="$(get_project_root)"
    local app_path="$project_root/src/wbgt_kiosk_en.py"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                cleanup_and_exit 0
                ;;
            --version|-v)
                show_version
                cleanup_and_exit 0
                ;;
            --demo|--gui)
                # Pass through to application
                break
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                show_help
                cleanup_and_exit 1
                ;;
        esac
        shift
    done
    
    # Check Python environment
    if ! check_python; then
        cleanup_and_exit 1 "Python environment check failed"
    fi
    
    # Check if application exists
    if ! check_file "$app_path" "English WBGT application"; then
        cleanup_and_exit 1 "Application not found"
    fi
    
    # Set up virtual environment
    setup_virtual_env
    
    # Run application
    log_message "Starting English WBGT Kiosk..." "INFO"
    python3 "$app_path" "$@"
    local exit_code=$?
    
    cleanup_and_exit $exit_code "English WBGT Kiosk completed with exit code: $exit_code"
}

# Run main function
main "$@"