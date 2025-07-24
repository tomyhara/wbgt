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

# Initialize success tracking
jma_success=0
wbgt_success=0
openweather_success=0

# Check if OpenWeatherMap API is configured
check_openweather_available() {
    python3 -c "
import sys, os
sys.path.append('$PROJECT_ROOT/setup')
try:
    from config_loader import load_config
    config = load_config()
    api_key = config.get('openweather_api_key', '')
    if api_key and api_key != 'YOUR_OPENWEATHERMAP_API_KEY_HERE':
        print('available')
    else:
        print('not_configured')
except Exception as e:
    print('error')
" 2>/dev/null
}

# Download OpenWeatherMap data (if configured)
openweather_status=$(check_openweather_available)
if [ "$openweather_status" = "available" ]; then
    log_to_file "$LOG_FILE" "Starting OpenWeatherMap weather data download..." "INFO"
    if "$SCRIPT_DIR/download_openweather_data.sh"; then
        log_to_file "$LOG_FILE" "OpenWeatherMap weather data download completed successfully" "SUCCESS"
        openweather_success=1
    else
        log_to_file "$LOG_FILE" "OpenWeatherMap weather data download failed" "ERROR"
        openweather_success=0
    fi
    sleep 2
else
    log_to_file "$LOG_FILE" "OpenWeatherMap API not configured, skipping weather data download" "WARN"
fi

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
total_downloads=$((jma_success + wbgt_success + openweather_success))

if [ $total_downloads -eq 3 ]; then
    cleanup_and_exit 0 "All data downloads completed successfully"
elif [ $total_downloads -eq 2 ]; then
    cleanup_and_exit 0 "Most data downloads completed successfully"
elif [ $total_downloads -eq 1 ]; then
    cleanup_and_exit 1 "Partial success: Some data downloads completed"
else
    cleanup_and_exit 2 "All data downloads failed"
fi