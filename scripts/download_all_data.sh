#!/bin/bash

# Master Download Script
# Downloads all CSV data for WBGT system offline fallback

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Initialize logging
PROJECT_ROOT="$(get_project_root)"
LOG_FILE="$PROJECT_ROOT/logs/master_download.log"
ensure_directory "$(dirname "$LOG_FILE")" "logs directory"

log_to_file "$LOG_FILE" "Master Data Download Started" "INFO"

# Download JMA weather data
log_to_file "$LOG_FILE" "Starting JMA weather data download..." "INFO"
if "$SCRIPT_DIR/download_jma_data.sh"; then
    log_to_file "$LOG_FILE" "JMA weather data download completed successfully" "SUCCESS"
    jma_success=1
else
    log_to_file "$LOG_FILE" "JMA weather data download failed" "ERROR"
    jma_success=0
fi

# Wait between downloads to avoid overwhelming servers
sleep 2

# Download Environment Ministry WBGT data
log_to_file "$LOG_FILE" "Starting Environment Ministry WBGT data download..." "INFO"
if "$SCRIPT_DIR/download_wbgt_data.sh"; then
    log_to_file "$LOG_FILE" "Environment Ministry WBGT data download completed successfully" "SUCCESS"
    wbgt_success=1
else
    log_to_file "$LOG_FILE" "Environment Ministry WBGT data download failed" "ERROR"
    wbgt_success=0
fi

# Summary and exit
log_to_file "$LOG_FILE" "Master Data Download Summary" "INFO"
if [ $jma_success -eq 1 ] && [ $wbgt_success -eq 1 ]; then
    cleanup_and_exit 0 "All data downloads completed successfully"
elif [ $jma_success -eq 1 ] || [ $wbgt_success -eq 1 ]; then
    cleanup_and_exit 1 "Partial success: Some data downloads completed"
else
    cleanup_and_exit 2 "All data downloads failed"
fi