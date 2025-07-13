#!/bin/bash

# Environment Ministry WBGT Data Download Script
# Downloads CSV data from Environment Ministry WBGT service for offline use when SSL issues occur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/csv"
LOG_FILE="$SCRIPT_DIR/../logs/wbgt_download.log"

# Create directories if they don't exist
mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to download WBGT forecast data
download_wbgt_forecast() {
    local prefecture="$1"
    
    log_message "Downloading WBGT forecast data for $prefecture"
    
    # Environment Ministry WBGT forecast URL
    local url="https://www.wbgt.env.go.jp/prev15WG/dl/yohou_${prefecture}.csv"
    local output_file="$DATA_DIR/wbgt_forecast_${prefecture}.csv"
    
    # Download with curl, handling SSL issues
    if curl -s --connect-timeout 10 --max-time 30 \
        --user-agent "WBGT-Kiosk/1.0 (WBGT Data Collection)" \
        --insecure \
        -o "$output_file" \
        "$url"; then
        
        if [ -s "$output_file" ]; then
            log_message "✅ Successfully downloaded WBGT forecast data for $prefecture"
            return 0
        else
            log_message "❌ Downloaded WBGT forecast file is empty for $prefecture"
            rm -f "$output_file"
            return 1
        fi
    else
        log_message "❌ Failed to download WBGT forecast data for $prefecture"
        return 1
    fi
}

# Function to download WBGT current data
download_wbgt_current() {
    local prefecture="$1"
    local year_month="$2"
    
    log_message "Downloading WBGT current data for $prefecture ($year_month)"
    
    # Environment Ministry WBGT current data URL
    local url="https://www.wbgt.env.go.jp/est15WG/dl/wbgt_${prefecture}_${year_month}.csv"
    local output_file="$DATA_DIR/wbgt_current_${prefecture}_${year_month}.csv"
    
    # Download with curl, handling SSL issues
    if curl -s --connect-timeout 10 --max-time 30 \
        --user-agent "WBGT-Kiosk/1.0 (WBGT Data Collection)" \
        --insecure \
        -o "$output_file" \
        "$url"; then
        
        if [ -s "$output_file" ]; then
            log_message "✅ Successfully downloaded WBGT current data for $prefecture ($year_month)"
            return 0
        else
            log_message "❌ Downloaded WBGT current file is empty for $prefecture ($year_month)"
            rm -f "$output_file"
            return 1
        fi
    else
        log_message "❌ Failed to download WBGT current data for $prefecture ($year_month)"
        return 1
    fi
}

# Function to download heat stroke alert data
download_heatstroke_alert() {
    local date_str="$1"
    local time_str="$2"
    local year="$3"
    
    log_message "Downloading heat stroke alert data for $date_str $time_str"
    
    # Environment Ministry alert data URL
    local url="https://www.wbgt.env.go.jp/alert/dl/${year}/alert_${date_str}_${time_str}.csv"
    local output_file="$DATA_DIR/alert_${date_str}_${time_str}.csv"
    
    # Download with curl, handling SSL issues
    if curl -s --connect-timeout 10 --max-time 30 \
        --user-agent "WBGT-Kiosk/1.0 (Alert Data Collection)" \
        --insecure \
        -o "$output_file" \
        "$url"; then
        
        if [ -s "$output_file" ]; then
            log_message "✅ Successfully downloaded alert data for $date_str $time_str"
            return 0
        else
            log_message "❌ Downloaded alert file is empty for $date_str $time_str"
            rm -f "$output_file"
            return 1
        fi
    else
        log_message "❌ Failed to download alert data for $date_str $time_str"
        return 1
    fi
}

# Main execution
log_message "=== Environment Ministry WBGT Data Download Started ==="

# Prefecture codes for major areas
PREFECTURES=(
    "tokyo"
    "kanagawa" 
    "osaka"
    "aichi"
    "fukuoka"
    "hokkaido"
    "miyagi"
)

# Get current date information
CURRENT_DATE=$(date '+%Y%m%d')
CURRENT_YEAR=$(date '+%Y')
CURRENT_MONTH=$(date '+%Y%m')
CURRENT_HOUR=$(date '+%H')

success_count=0
total_count=0

# Download forecast data for each prefecture
for prefecture in "${PREFECTURES[@]}"; do
    if download_wbgt_forecast "$prefecture"; then
        ((success_count++))
    fi
    ((total_count++))
    sleep 1  # Rate limiting
done

# Download current data for each prefecture
for prefecture in "${PREFECTURES[@]}"; do
    if download_wbgt_current "$prefecture" "$CURRENT_MONTH"; then
        ((success_count++))
    fi
    ((total_count++))
    sleep 1  # Rate limiting
done

# Download alert data based on current time
if [ "$CURRENT_HOUR" -lt 5 ]; then
    # Before 5 AM: use previous day 17:00 file
    ALERT_DATE=$(date -d 'yesterday' '+%Y%m%d')
    ALERT_TIME="17"
elif [ "$CURRENT_HOUR" -lt 14 ]; then
    # Before 14:00: use current day 05:00 file
    ALERT_DATE="$CURRENT_DATE"
    ALERT_TIME="05"
elif [ "$CURRENT_HOUR" -lt 17 ]; then
    # Before 17:00: use current day 14:00 file
    ALERT_DATE="$CURRENT_DATE"
    ALERT_TIME="14"
else
    # After 17:00: use current day 17:00 file
    ALERT_DATE="$CURRENT_DATE"
    ALERT_TIME="17"
fi

if download_heatstroke_alert "$ALERT_DATE" "$ALERT_TIME" "$CURRENT_YEAR"; then
    ((success_count++))
fi
((total_count++))

log_message "=== Environment Ministry WBGT Data Download Completed ==="
log_message "Success: $success_count/$total_count downloads"

# Exit with error if any downloads failed
if [ $success_count -eq $total_count ]; then
    log_message "All downloads successful"
    exit 0
else
    log_message "Some downloads failed"
    exit 1
fi