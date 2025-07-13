# CSV Mode Usage Guide

This guide explains how to use the WBGT system with local CSV data instead of direct API calls, which is useful when SSL certificate issues prevent direct API access.

## Overview

The system now supports a "CSV mode" where data is downloaded separately using bash scripts and then read by the Python applications. This approach bypasses SSL certificate issues that may occur in corporate environments.

## Quick Start

### 1. Download CSV Data Only
```bash
./scripts/run_with_csv.sh --download-only
```

### 2. Run with CSV Data (Japanese)
```bash
./scripts/run_with_csv.sh
```

### 3. Run with CSV Data (English)
```bash
./scripts/run_with_csv.sh --english
```

### 4. Use Existing CSV Data (No Download)
```bash
./scripts/run_with_csv.sh --run-only
```

## Available Scripts

### Master Scripts
- `./scripts/run_with_csv.sh` - Main script with options for download and execution
- `./scripts/download_all_data.sh` - Downloads all data sources

### Individual Download Scripts
- `./scripts/download_jma_data.sh` - Downloads JMA weather forecast data
- `./scripts/download_wbgt_data.sh` - Downloads Environment Ministry WBGT data

## How It Works

### Data Sources
The system downloads data from these sources:
1. **JMA (Japan Meteorological Agency)**
   - Weather forecast data for major cities
   - Observation station data
   - Files: `jma_forecast_XXXXXX.json`, `jma_amedas_table.json`

2. **Environment Ministry WBGT Service**
   - WBGT forecast data by prefecture
   - WBGT current data by prefecture and month
   - Heat stroke alert data by date and time
   - Files: `wbgt_forecast_*.csv`, `wbgt_current_*.csv`, `alert_*.csv`

### Force CSV Mode
When the environment variable `FORCE_CSV_MODE=1` is set, the Python APIs will:
1. Skip SSL-dependent HTTP requests
2. Read data directly from local CSV/JSON files
3. Log that forced CSV mode is enabled

### File Locations
- Downloaded data: `./data/csv/`
- Log files: `./logs/`

## Manual Usage

### Set CSV Mode in Python
```python
import os
os.environ['FORCE_CSV_MODE'] = '1'

# Now all API calls will use CSV data
from env_wbgt_api import EnvWBGTAPI
api = EnvWBGTAPI()
data = api.get_wbgt_forecast_data()
```

### Download Specific Data
```bash
# Download only JMA weather data
./scripts/download_jma_data.sh

# Download only WBGT data
./scripts/download_wbgt_data.sh

# Download all data
./scripts/download_all_data.sh
```

## Configuration

### Prefecture Mapping
WBGT data is downloaded for these prefectures by default:
- Tokyo (tokyo)
- Kanagawa (kanagawa)
- Osaka (osaka)
- Aichi (aichi)
- Fukuoka (fukuoka)
- Hokkaido (hokkaido)
- Miyagi (miyagi)

### JMA Area Codes
Weather data is downloaded for these areas:
- Tokyo (130000)
- Yokohama (140000)
- Osaka (270000)
- Nagoya (230000)
- Fukuoka (400000)
- Sapporo (016000)
- Sendai (040000)

## Data Freshness

The system checks file modification times:
- **JMA data**: Must be updated within 24 hours
- **WBGT forecast data**: Must be updated within 24 hours
- **WBGT current data**: Must be updated within 6 hours
- **Alert data**: Must be updated within 24 hours

## Troubleshooting

### If downloads fail
1. Check internet connectivity
2. Verify URLs are accessible (government sites may have maintenance)
3. Check log files in `./logs/` for detailed error messages

### If CSV reading fails
1. Ensure CSV files exist in `./data/csv/`
2. Check file permissions
3. Verify file modification times (old files are rejected)

### Location Code Issues
If you see "地点番号 XXXXX がヘッダーに見つかりません" errors:
1. Check the location code in your configuration
2. Verify the downloaded CSV contains your area's data
3. Update location codes in `setup/config.py` if needed

## Testing

Test CSV mode functionality:
```bash
python3 test_csv_mode.py
```

This will verify that all APIs can read from CSV files correctly.

## Integration with Existing Scripts

The existing scripts (`wbgt.sh`, `run_wbgt.sh`, etc.) continue to work normally. The CSV mode is an additional option for when direct API access fails.

## Security Note

The download scripts use `--insecure` flag with curl to bypass SSL certificate verification. This is intentional for environments with SSL issues, but be aware that this reduces security. The data sources are official government sites, which reduces the security risk.