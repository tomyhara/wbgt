#!/bin/bash
# WBGT キオスク実行スクリプト（日本語版）
# WBGT Kiosk Runner Script (Japanese Version)

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Show help function
show_help() {
    show_header "WBGT熱中症警戒キオスク (日本語版) / WBGT Heat Stroke Warning Kiosk (Japanese)"
    
    print_colored white "使用方法 / Usage:"
    echo "  $0 [OPTIONS]"
    echo
    print_colored yellow "オプション / Options:"
    echo "  --demo              デモモード (3回更新で終了) / Demo mode (3 updates then exit)"
    echo "  --gui               GUI版 (実験的) / GUI version (experimental)"
    echo "  --help, -h          ヘルプ表示 / Show this help"
    echo "  --version, -v       バージョン情報 / Version information"
    echo
    print_colored yellow "例 / Examples:"
    echo "  $0                  通常モード / Normal mode"
    echo "  $0 --demo          デモモード / Demo mode"
    echo "  $0 --gui           GUI版 / GUI version"
    echo
    print_colored green "設定 / Configuration:"
    echo "  設定ファイル: setup/config.json または setup/config.py"
    echo "  Config file: setup/config.json or setup/config.py"
}

# Show version
show_version() {
    show_header "WBGT熱中症警戒キオスク (日本語版)"
    print_colored green "Version: 2.0.0"
    print_colored cyan "Language: Japanese (日本語)"
}

# Main function
main() {
    local project_root="$(get_project_root)"
    local app_path="$project_root/src/wbgt_kiosk.py"
    local app_args=()
    
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
                app_args+=("$1")
                shift
                ;;
            *)
                log_message "Unknown option: $1" "ERROR"
                show_help
                cleanup_and_exit 1
                ;;
        esac
    done
    
    # Check Python environment
    if ! check_python; then
        cleanup_and_exit 1 "Python environment check failed"
    fi
    
    # Check if application exists
    if ! check_file "$app_path" "Japanese WBGT application"; then
        cleanup_and_exit 1 "Application not found"
    fi
    
    # Set up virtual environment
    setup_virtual_env
    
    # Run application
    log_message "Starting Japanese WBGT Kiosk..." "INFO"
    python3 "$app_path" "${app_args[@]}"
    local exit_code=$?
    
    cleanup_and_exit $exit_code "Japanese WBGT Kiosk completed with exit code: $exit_code"
}

# Run main function
main "$@"
