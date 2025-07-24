#!/bin/bash

# JMA Weather Data Download Script
# Downloads CSV data from JMA API for offline use when SSL issues occur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/csv"
LOG_FILE="$SCRIPT_DIR/../logs/jma_download.log"

# Create directories if they don't exist
mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to download JMA forecast data
download_jma_forecast() {
    local area_code="$1"
    local area_name="$2"
    
    log_message "Downloading JMA forecast data for $area_name ($area_code)"
    
    # JMA forecast API URL
    local url="https://www.jma.go.jp/bosai/forecast/data/forecast/${area_code}.json"
    local output_file="$DATA_DIR/jma_forecast_${area_code}.json"
    
    # Download with curl, handling SSL issues
    if curl -s --connect-timeout 10 --max-time 30 \
        --user-agent "WBGT-Kiosk/1.0 (Weather Data Collection)" \
        --insecure \
        -o "$output_file" \
        "$url"; then
        
        if [ -s "$output_file" ]; then
            log_message "✅ Successfully downloaded forecast data for $area_name"
            return 0
        else
            log_message "❌ Downloaded file is empty for $area_name"
            rm -f "$output_file"
            return 1
        fi
    else
        log_message "❌ Failed to download forecast data for $area_name"
        return 1
    fi
}

# Function to download JMA observation data
download_jma_observation() {
    log_message "Downloading JMA observation station data"
    
    local url="https://www.jma.go.jp/bosai/amedas/const/amedastable.json"
    local output_file="$DATA_DIR/jma_amedas_table.json"
    
    if curl -s --connect-timeout 10 --max-time 30 \
        --user-agent "WBGT-Kiosk/1.0 (Weather Data Collection)" \
        --insecure \
        -o "$output_file" \
        "$url"; then
        
        if [ -s "$output_file" ]; then
            log_message "✅ Successfully downloaded observation station data"
            return 0
        else
            log_message "❌ Downloaded observation file is empty"
            rm -f "$output_file"
            return 1
        fi
    else
        log_message "❌ Failed to download observation station data"
        return 1
    fi
}

# Main execution
log_message "=== JMA Data Download Started ==="

# Get area codes from configuration
log_message "Reading area codes from configuration..."
CONFIG_DATA=$(python3 "$SCRIPT_DIR/get_config.py" area_codes 2>/dev/null)

if [ -z "$CONFIG_DATA" ]; then
    log_message "Warning: No configuration found, using default area codes"
    # Fallback to default area codes
    AREA_CODES=("130000" "140000" "270000" "230000" "400000" "016000" "040000")
    AREA_NAMES=("Tokyo" "Yokohama" "Osaka" "Nagoya" "Fukuoka" "Sapporo" "Sendai")
else
    # Parse configuration data
    AREA_CODES=()
    AREA_NAMES=()
    while IFS=':' read -r area_code area_name; do
        if [ -n "$area_code" ] && [ -n "$area_name" ]; then
            AREA_CODES+=("$area_code")
            AREA_NAMES+=("$area_name")
        fi
    done <<< "$CONFIG_DATA"
    
    # Add default areas if none configured
    if [ ${#AREA_CODES[@]} -eq 0 ]; then
        log_message "Warning: No areas configured, using defaults"
        AREA_CODES=("130000" "140000" "270000" "230000" "400000" "016000" "040000")
        AREA_NAMES=("Tokyo" "Yokohama" "Osaka" "Nagoya" "Fukuoka" "Sapporo" "Sendai")
    fi
fi

log_message "Downloading data for ${#AREA_CODES[@]} configured areas"

# Download forecast data for configured areas
success_count=0
total_count=${#AREA_CODES[@]}

for i in "${!AREA_CODES[@]}"; do
    area_code="${AREA_CODES[$i]}"
    area_name="${AREA_NAMES[$i]}"
    if download_jma_forecast "$area_code" "$area_name"; then
        ((success_count++))
    fi
    sleep 1  # Rate limiting
done

# Download observation data
if download_jma_observation; then
    ((success_count++))
    ((total_count++))
fi

log_message "=== JMA Data Download Completed ==="
log_message "Success: $success_count/$total_count downloads"

# Exit with error if any downloads failed
if [ $success_count -eq $total_count ]; then
    log_message "All downloads successful"
    exit 0
else
    log_message "Some downloads failed"
    exit 1
fi