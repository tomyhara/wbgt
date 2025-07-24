#!/bin/bash
# Common functions for WBGT scripts
# 共通機能ライブラリ

# Script directory detection
get_script_dir() {
    echo "$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
}

# Project root directory
get_project_root() {
    local script_dir="$(get_script_dir)"
    echo "$(cd "$script_dir/.." && pwd)"
}

# Color output functions
print_colored() {
    local color=$1
    local text=$2
    case $color in
        red)     echo -e "\033[91m$text\033[0m" ;;
        green)   echo -e "\033[92m$text\033[0m" ;;
        yellow)  echo -e "\033[93m$text\033[0m" ;;
        blue)    echo -e "\033[94m$text\033[0m" ;;
        magenta) echo -e "\033[95m$text\033[0m" ;;
        cyan)    echo -e "\033[96m$text\033[0m" ;;
        white)   echo -e "\033[97m$text\033[0m" ;;
        bold)    echo -e "\033[1m$text\033[0m" ;;
        *)       echo "$text" ;;
    esac
}

# Logging function with timestamps
log_message() {
    local level=${2:-"INFO"}
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        ERROR)   print_colored red "[$timestamp] ERROR: $message" ;;
        WARN)    print_colored yellow "[$timestamp] WARN: $message" ;;
        SUCCESS) print_colored green "[$timestamp] SUCCESS: $message" ;;
        INFO)    print_colored cyan "[$timestamp] INFO: $message" ;;
        DEBUG)   echo "[$timestamp] DEBUG: $message" ;;
        *)       echo "[$timestamp] $message" ;;
    esac
}

# Log to file and console
log_to_file() {
    local log_file="$1"
    local message="$2"
    local level="${3:-INFO}"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$log_file")"
    
    # Log to console
    log_message "$message" "$level"
    
    # Log to file
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$log_file"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_message "Python version: $version" "INFO"
        return 0
    elif command_exists python; then
        local version=$(python --version 2>&1 | cut -d' ' -f2)
        if [[ $version == 3.* ]]; then
            log_message "Python version: $version" "INFO"
            return 0
        else
            log_message "Python 3 is required, found: $version" "ERROR"
            return 1
        fi
    else
        log_message "Python 3 is not installed" "ERROR"
        return 1
    fi
}

# Virtual environment setup and activation
setup_virtual_env() {
    local project_root="$(get_project_root)"
    local venv_path="$project_root/venv"
    
    if [ -d "$venv_path" ]; then
        log_message "Activating virtual environment..." "INFO"
        source "$venv_path/bin/activate"
        
        # Verify activation
        if [[ "$VIRTUAL_ENV" == "$venv_path" ]]; then
            log_message "Virtual environment activated: $VIRTUAL_ENV" "SUCCESS"
            return 0
        else
            log_message "Failed to activate virtual environment" "WARN"
            return 1
        fi
    else
        log_message "Virtual environment not found at: $venv_path" "WARN"
        log_message "Using system Python. Consider running: ./setup/setup_venv.sh" "INFO"
        return 1
    fi
}

# Check if file exists and is readable
check_file() {
    local file_path="$1"
    local description="${2:-file}"
    
    if [ -f "$file_path" ] && [ -r "$file_path" ]; then
        return 0
    else
        log_message "$description not found or not readable: $file_path" "ERROR"
        return 1
    fi
}

# Check if directory exists and is writable
check_directory() {
    local dir_path="$1"
    local description="${2:-directory}"
    
    if [ -d "$dir_path" ] && [ -w "$dir_path" ]; then
        return 0
    elif [ -d "$dir_path" ]; then
        log_message "$description exists but is not writable: $dir_path" "ERROR"
        return 1
    else
        log_message "$description does not exist: $dir_path" "ERROR"
        return 1
    fi
}

# Create directory if it doesn't exist
ensure_directory() {
    local dir_path="$1"
    local description="${2:-directory}"
    
    if [ ! -d "$dir_path" ]; then
        if mkdir -p "$dir_path" 2>/dev/null; then
            log_message "Created $description: $dir_path" "SUCCESS"
        else
            log_message "Failed to create $description: $dir_path" "ERROR"
            return 1
        fi
    fi
    return 0
}

# System language detection
detect_system_language() {
    local lang="${LANG:-${LC_ALL:-${LC_MESSAGES:-}}}"
    
    if [[ "$lang" =~ ^ja ]]; then
        echo "ja"
    elif [[ "$lang" =~ ^en ]]; then
        echo "en"
    else
        # Default to English
        echo "en"
    fi
}

# Validate command line arguments
validate_args() {
    local valid_options=("$@")
    local is_valid=false
    
    for valid_option in "${valid_options[@]}"; do
        if [[ "$1" == "$valid_option" ]]; then
            is_valid=true
            break
        fi
    done
    
    if [ "$is_valid" = false ]; then
        log_message "Invalid option: $1" "ERROR"
        return 1
    fi
    
    return 0
}

# Show script header
show_header() {
    local title="$1"
    local version="${2:-2.0.0}"
    
    print_colored cyan "=================================================================="
    print_colored bold "  🌡️  $title"
    print_colored cyan "  Version $version - $(date '+%Y-%m-%d')"
    print_colored cyan "=================================================================="
    echo
}

# Show script footer
show_footer() {
    local status="$1"
    echo
    print_colored cyan "=================================================================="
    if [ "$status" = "success" ]; then
        print_colored green "  ✅ Script completed successfully"
    elif [ "$status" = "error" ]; then
        print_colored red "  ❌ Script completed with errors"
    else
        print_colored blue "  ℹ️  Script completed"
    fi
    print_colored cyan "=================================================================="
}

# Cleanup function for script exit
cleanup_and_exit() {
    local exit_code="${1:-0}"
    local message="${2:-}"
    
    if [ -n "$message" ]; then
        if [ "$exit_code" -eq 0 ]; then
            log_message "$message" "SUCCESS"
            show_footer "success"
        else
            log_message "$message" "ERROR"
            show_footer "error"
        fi
    fi
    
    exit "$exit_code"
}