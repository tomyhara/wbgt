#!/bin/bash

# WBGT System with CSV Data Runner
# This script downloads fresh CSV data and runs the WBGT system using local files

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../logs/run_with_csv.log"

# Create directories if they don't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --download-only    Only download CSV data, don't run Python scripts"
    echo "  -r, --run-only        Only run Python scripts with existing CSV data"
    echo "  -e, --english         Run English version"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Default: Download CSV data and run Japanese version"
}

# Parse command line arguments
DOWNLOAD_ONLY=false
RUN_ONLY=false
ENGLISH=false

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
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

log_message "=== WBGT CSV Runner Started ==="

# Download CSV data if not run-only mode
if [ "$RUN_ONLY" = false ]; then
    log_message "Downloading fresh CSV data..."
    
    if "$SCRIPT_DIR/download_all_data.sh"; then
        log_message "✅ CSV data download completed successfully"
    else
        log_message "❌ CSV data download failed, but will try to use existing data"
    fi
else
    log_message "Skipping download, using existing CSV data"
fi

# Stop here if download-only mode
if [ "$DOWNLOAD_ONLY" = true ]; then
    log_message "Download-only mode: Stopping here"
    exit 0
fi

# Run Python scripts with CSV data
log_message "Running WBGT system with CSV data..."

# Set environment variable to force CSV usage
export FORCE_CSV_MODE=1

if [ "$ENGLISH" = true ]; then
    log_message "Running English version..."
    python3 "$SCRIPT_DIR/../src/wbgt_kiosk_en.py"
else
    log_message "Running Japanese version..."
    python3 "$SCRIPT_DIR/../src/wbgt_kiosk.py"
fi

log_message "=== WBGT CSV Runner Completed ==="