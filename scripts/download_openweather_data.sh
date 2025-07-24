#!/bin/bash
# OpenWeatherMap天気データダウンロードスクリプト
# OpenWeatherMap Weather Data Download Script

# Load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Configuration
PROJECT_ROOT="$(get_project_root)"
CSV_DIR="$PROJECT_ROOT/data/csv"
OPENWEATHER_DIR="$CSV_DIR/openweather"
CONFIG_SCRIPT="$SCRIPT_DIR/get_config.py"
LOG_FILE="$PROJECT_ROOT/openweather_download.log"

# OpenWeatherMap API settings
API_BASE_URL="https://api.openweathermap.org/data/2.5"
TIMEOUT=30

# Initialize
show_header "OpenWeatherMap天気データダウンロード / OpenWeatherMap Weather Data Download"

# Check Python environment
if ! check_python; then
    cleanup_and_exit 1 "Python environment check failed"
fi

# Setup virtual environment
setup_virtual_env

# Create directories
mkdir -p "$OPENWEATHER_DIR"
mkdir -p "$CSV_DIR"

# Get API key from configuration
get_api_key() {
    python3 -c "
import sys, os
sys.path.append('$PROJECT_ROOT/setup')
try:
    from config_loader import load_config
    config = load_config()
    api_key = config.get('openweather_api_key', '')
    if api_key and api_key != 'YOUR_OPENWEATHERMAP_API_KEY_HERE':
        print(api_key)
    else:
        exit(1)
except Exception as e:
    exit(1)
" 2>/dev/null
}

# Get locations from configuration
get_locations() {
    python3 "$CONFIG_SCRIPT" locations 2>/dev/null || {
        echo "横浜,35.4478,139.6425"
        echo "銚子,35.7347,140.8317"
    }
}

# Download weather data for a location
download_weather_data() {
    local name="$1"
    local lat="$2"
    local lon="$3"
    local api_key="$4"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    log_message "Downloading weather data for $name ($lat, $lon)" "INFO"
    
    # Current weather
    local current_url="${API_BASE_URL}/weather?lat=${lat}&lon=${lon}&appid=${api_key}&units=metric&lang=ja"
    local current_file="${OPENWEATHER_DIR}/${name}_current_${timestamp}.json"
    
    if curl -s --connect-timeout $TIMEOUT --max-time $TIMEOUT "$current_url" -o "$current_file"; then
        if [ -s "$current_file" ] && jq empty "$current_file" 2>/dev/null; then
            log_message "Successfully downloaded current weather for $name" "SUCCESS"
        else
            log_message "Invalid current weather data for $name" "ERROR"
            rm -f "$current_file"
            return 1
        fi
    else
        log_message "Failed to download current weather for $name" "ERROR"
        return 1
    fi
    
    # Forecast data
    local forecast_url="${API_BASE_URL}/forecast?lat=${lat}&lon=${lon}&appid=${api_key}&units=metric&lang=ja"
    local forecast_file="${OPENWEATHER_DIR}/${name}_forecast_${timestamp}.json"
    
    if curl -s --connect-timeout $TIMEOUT --max-time $TIMEOUT "$forecast_url" -o "$forecast_file"; then
        if [ -s "$forecast_file" ] && jq empty "$forecast_file" 2>/dev/null; then
            log_message "Successfully downloaded forecast for $name" "SUCCESS"
        else
            log_message "Invalid forecast data for $name" "ERROR"
            rm -f "$forecast_file"
            return 1
        fi
    else
        log_message "Failed to download forecast for $name" "ERROR"
        return 1
    fi
    
    # Create symlinks to latest data
    local current_latest="${OPENWEATHER_DIR}/${name}_current_latest.json"
    local forecast_latest="${OPENWEATHER_DIR}/${name}_forecast_latest.json"
    
    ln -sf "$(basename "$current_file")" "$current_latest"
    ln -sf "$(basename "$forecast_file")" "$forecast_latest"
    
    return 0
}

# Main execution
main() {
    log_message "OpenWeatherMap data download started" "INFO"
    
    # Check for required tools
    if ! command -v curl >/dev/null 2>&1; then
        print_colored red "❌ curl command not found. Please install curl."
        cleanup_and_exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        print_colored yellow "⚠️  jq command not found. JSON validation will be skipped."
    fi
    
    # Get API key
    API_KEY=$(get_api_key)
    if [ -z "$API_KEY" ]; then
        print_colored red "❌ OpenWeatherMap API key not found or not configured."
        print_colored yellow "   Please set 'openweather_api_key' in setup/config.json"
        cleanup_and_exit 1
    fi
    
    log_message "API key found, starting downloads..." "INFO"
    
    # Download data for each location
    local success_count=0
    local total_count=0
    
    while IFS=',' read -r name lat lon || [ -n "$name" ]; do
        # Skip empty lines
        [ -z "$name" ] && continue
        
        total_count=$((total_count + 1))
        print_colored cyan "📡 Downloading weather data for $name..."
        
        if download_weather_data "$name" "$lat" "$lon" "$API_KEY"; then
            success_count=$((success_count + 1))
            print_colored green "✅ $name - Download completed"
        else
            print_colored red "❌ $name - Download failed"
        fi
        
        # Rate limiting - OpenWeatherMap free tier allows 60 calls/minute
        sleep 1
        
    done < <(get_locations)
    
    # Generate summary
    log_message "Download completed: $success_count/$total_count locations successful" "INFO"
    
    if [ $success_count -eq $total_count ]; then
        print_colored green "🎉 All weather data downloads completed successfully!"
        
        # Create download summary
        cat > "$OPENWEATHER_DIR/download_summary.txt" << EOF
OpenWeatherMap Weather Data Download Summary
===========================================
Download Date: $(date)
Total Locations: $total_count
Successful Downloads: $success_count
Data Directory: $OPENWEATHER_DIR

Files Downloaded:
$(ls -la "$OPENWEATHER_DIR"/*.json 2>/dev/null | head -20)

Latest Data Links:
$(ls -la "$OPENWEATHER_DIR"/*_latest.json 2>/dev/null)
EOF
        
        cleanup_and_exit 0 "All downloads completed successfully"
    else
        print_colored yellow "⚠️  Some downloads failed. Check $LOG_FILE for details."
        cleanup_and_exit 1 "Partial download failure"
    fi
}

# Cleanup old files (keep last 10 downloads per location)
cleanup_old_files() {
    log_message "Cleaning up old weather data files..." "INFO"
    
    for location in $(get_locations | cut -d',' -f1); do
        # Keep only the latest 10 files for each location and type
        for type in current forecast; do
            ls -t "$OPENWEATHER_DIR/${location}_${type}_"*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
        done
    done
}

# Run cleanup before download
cleanup_old_files

# Execute main function
main

# Final cleanup
cleanup_old_files