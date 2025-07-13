#!/bin/bash

# Master Download Script
# Downloads all CSV data for WBGT system offline fallback

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/master_download.log"

# Create directories if they don't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "=== Master Data Download Started ==="

# Download JMA weather data
log_message "Starting JMA weather data download..."
if "$SCRIPT_DIR/download_jma_data.sh"; then
    log_message "✅ JMA weather data download completed successfully"
    jma_success=1
else
    log_message "❌ JMA weather data download failed"
    jma_success=0
fi

# Wait between downloads
sleep 2

# Download Environment Ministry WBGT data
log_message "Starting Environment Ministry WBGT data download..."
if "$SCRIPT_DIR/download_wbgt_data.sh"; then
    log_message "✅ Environment Ministry WBGT data download completed successfully"
    wbgt_success=1
else
    log_message "❌ Environment Ministry WBGT data download failed"
    wbgt_success=0
fi

# Summary
log_message "=== Master Data Download Summary ==="
if [ $jma_success -eq 1 ] && [ $wbgt_success -eq 1 ]; then
    log_message "🎉 All data downloads completed successfully"
    exit 0
elif [ $jma_success -eq 1 ] || [ $wbgt_success -eq 1 ]; then
    log_message "⚠️ Partial success: Some data downloads completed"
    exit 1
else
    log_message "❌ All data downloads failed"
    exit 2
fi