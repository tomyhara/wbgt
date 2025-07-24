#!/bin/bash

# WBGT System with CSV Data Runner
# This script downloads fresh CSV data and runs the WBGT system using local files

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Initialize logging
PROJECT_ROOT="$(get_project_root)"
LOG_FILE="$PROJECT_ROOT/logs/run_with_csv.log"
ensure_directory "$(dirname "$LOG_FILE")" "logs directory"

# Function to show usage
show_usage() {
    show_header "WBGT CSV Mode Runner / WBGT CSV モード実行"
    
    print_colored white "使用方法 / Usage:"
    echo "  $0 [OPTIONS]"
    echo
    print_colored yellow "オプション / Options:"
    echo "  -d, --download-only    CSVデータのみダウンロード / Only download CSV data"
    echo "  -r, --run-only         既存CSVデータで実行 / Run with existing CSV data"
    echo "  -e, --english          英語版を実行 / Run English version"
    echo "  -g, --gui              GUI版で実行 / Run in GUI mode"
    echo "  -h, --help             ヘルプ表示 / Show this help"
    echo "  -v, --verbose          詳細ログ / Verbose logging"
    echo
    print_colored yellow "例 / Examples:"
    echo "  $0                     CSVダウンロード後、日本語版実行"
    echo "  $0 --download-only     CSVデータのみダウンロード"
    echo "  $0 --run-only --english 既存CSVで英語版実行"
    echo "  $0 --english --gui     CSVダウンロード後、英語版GUI実行"
    echo
    print_colored green "データソース / Data Sources:"
    echo "  • 環境省熱中症予防情報サイト / Ministry of Environment WBGT"
    echo "  • 気象庁API / Japan Meteorological Agency API"
    echo "  設定: setup/config.json または setup/config.py"
}

# Parse command line arguments
DOWNLOAD_ONLY=false
RUN_ONLY=false
ENGLISH=false
GUI=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--download-only)
            DOWNLOAD_ONLY=true
            shift
            ;;
        -r|--run-only)
            RUN_ONLY=true
            shift
            ;;
        -e|--english)
            ENGLISH=true
            shift
            ;;
        -g|--gui)
            GUI=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            cleanup_and_exit 0
            ;;
        *)
            log_message "Unknown option: $1" "ERROR"
            show_usage
            cleanup_and_exit 1
            ;;
    esac
done

# Start logging
log_to_file "$LOG_FILE" "WBGT CSV Runner Started" "INFO"

# Check Python environment
if ! check_python; then
    cleanup_and_exit 1 "Python environment check failed"
fi

# Download CSV data if not run-only mode
if [ "$RUN_ONLY" = false ]; then
    log_to_file "$LOG_FILE" "Starting CSV data download..." "INFO"
    
    if [ "$VERBOSE" = true ]; then
        "$SCRIPT_DIR/download_all_data.sh" 2>&1 | tee -a "$LOG_FILE"
        download_result=${PIPESTATUS[0]}
    else
        "$SCRIPT_DIR/download_all_data.sh" >> "$LOG_FILE" 2>&1
        download_result=$?
    fi
    
    if [ $download_result -eq 0 ]; then
        log_to_file "$LOG_FILE" "CSV data download completed successfully" "SUCCESS"
    else
        log_to_file "$LOG_FILE" "CSV data download failed, but will try to use existing data" "WARN"
    fi
else
    log_to_file "$LOG_FILE" "Skipping download, using existing CSV data" "INFO"
fi

# Stop here if download-only mode
if [ "$DOWNLOAD_ONLY" = true ]; then
    log_to_file "$LOG_FILE" "Download-only mode: Stopping here" "INFO"
    cleanup_and_exit 0 "Download completed"
fi

# Check if CSV data exists
CSV_DIR="$PROJECT_ROOT/data/csv"
if [ ! -d "$CSV_DIR" ] || [ -z "$(ls -A "$CSV_DIR" 2>/dev/null)" ]; then
    log_to_file "$LOG_FILE" "No CSV data found in $CSV_DIR" "ERROR"
    log_to_file "$LOG_FILE" "Please run with --download-only first to download data" "ERROR"
    cleanup_and_exit 1 "No CSV data available"
fi

# Set up virtual environment
setup_virtual_env

# Run Python scripts with CSV data
log_to_file "$LOG_FILE" "Running WBGT system with CSV data..." "INFO"

# Set environment variable to force CSV usage
export FORCE_CSV_MODE=1

# Determine which application to run
if [ "$ENGLISH" = true ]; then
    APP_PATH="$PROJECT_ROOT/src/wbgt_kiosk_en.py"
    log_to_file "$LOG_FILE" "Starting English version with CSV data..." "INFO"
else
    APP_PATH="$PROJECT_ROOT/src/wbgt_kiosk.py"
    log_to_file "$LOG_FILE" "Starting Japanese version with CSV data..." "INFO"
fi

# Check if application exists
if ! check_file "$APP_PATH" "WBGT application"; then
    cleanup_and_exit 1 "Application not found"
fi

# Prepare application arguments
APP_ARGS=()
if [ "$GUI" = true ]; then
    APP_ARGS+=(--gui)
fi

# Run the application
if [ "$VERBOSE" = true ]; then
    python3 "$APP_PATH" "${APP_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
    app_exit_code=${PIPESTATUS[0]}
else
    python3 "$APP_PATH" "${APP_ARGS[@]}" >> "$LOG_FILE" 2>&1
    app_exit_code=$?
fi

# Report completion
if [ $app_exit_code -eq 0 ]; then
    log_to_file "$LOG_FILE" "WBGT CSV Runner completed successfully" "SUCCESS"
    cleanup_and_exit 0 "CSV mode execution completed successfully"
else
    log_to_file "$LOG_FILE" "WBGT CSV Runner completed with errors (exit code: $app_exit_code)" "ERROR"
    cleanup_and_exit $app_exit_code "CSV mode execution failed"
fi