# WBGT Heat Stroke Warning Kiosk (English Version)

A professional kiosk system for displaying heat stroke warning information and weather data, supporting multiple locations with real-time WBGT (Wet Bulb Globe Temperature) index monitoring.

## 🌡️ Features

- **Real-time WBGT Index**: Official data from Japan's Ministry of the Environment
- **Multi-location Support**: Monitor multiple cities simultaneously
- **Heat Stroke Alerts**: Official warning information display
- **Weather Information**: Current conditions from JMA (Japan Meteorological Agency)
- **Professional Display**: Color-coded warning levels and clean interface
- **Cross-platform**: Runs on Linux, macOS, and Windows
- **Multiple Modes**: Terminal and GUI versions available
- **CSV Mode**: Offline operation for SSL certificate issues

## 📋 Requirements

- Python 3.8 or higher
- Internet connection
- Operating System: Linux, macOS, or Windows

## 🚀 Quick Start

### 1. Download the Repository
```bash
git clone [repository-url]
cd wbgt
```

### 2. Install Dependencies
```bash
pip install -r setup/requirements.txt
```

### 3. Configure Settings
```bash
cp setup/config_en.sample.py setup/config_en.py
# Edit setup/config_en.py to set your monitoring locations
```

### 4. Run Demo
```bash
python src/wbgt_kiosk_en.py --demo
```

## ⚙️ Configuration

### JSON Configuration (Recommended)

Edit `setup/config.json` to customize your setup:

```json
{
  "locations": [
    {
      "name": "Tokyo",
      "area_code": "130000",
      "wbgt_location_code": "44132",
      "prefecture": "Tokyo"
    },
    {
      "name": "Yokohama", 
      "area_code": "140000",
      "wbgt_location_code": "46106",
      "prefecture": "Kanagawa"
    }
  ],
  "update_interval_minutes": 30,
  "display": {
    "width": 800,
    "height": 600,
    "fullscreen": false
  },
  "openweather_api_key": "YOUR_OPENWEATHERMAP_API_KEY_HERE",
  "weather_api": {
    "provider": "openweathermap",
    "fallback_to_jma": true,
    "timeout": 10
  }
}
```

#### OpenWeatherMap API Key Setup

1. **Get API Key**:
   - Create account at [OpenWeatherMap](https://openweathermap.org/api)
   - Free plan: 1,000 calls/day
   - Get key from API Keys page

2. **Update Configuration**:
   ```bash
   # Edit config.json
   nano setup/config.json
   
   # Replace "YOUR_OPENWEATHERMAP_API_KEY_HERE" with actual key
   "openweather_api_key": "abcd1234your_actual_api_key_here"
   ```

3. **Easy Setup Script**:
   ```bash
   # Interactive API key setup
   ./scripts/setup_openweather_api.sh
   ```

4. **Test Configuration**:
   ```bash
   # Test OpenWeatherMap data
   python3 test_openweather_offline.py
   ```

**Note**: If API key is not configured, the system automatically falls back to offline mode or JMA API.

### Python Configuration (Legacy)

Edit `setup/config_en.py`:

```python
LOCATIONS = [
    {
        'name': 'Tokyo',
        'area_code': '130000',
        'prefecture': 'Tokyo',
        'wbgt_location_code': '44132'
    }
]
```

### Finding Location Codes

**JMA Area Codes** (Major Cities):
- Tokyo: 130000
- Yokohama: 140000  
- Osaka: 270000
- Nagoya: 230000
- Sapporo: 016000

**Environment Ministry WBGT Codes**:
- Tokyo (Otemachi): 44132
- Yokohama: 45132
- Osaka: 47772
- Nagoya: 47636

## 🎮 Usage

### Terminal Mode (Default)
```bash
python src/wbgt_kiosk_en.py
```

### Demo Mode (3 updates then exit)
```bash
python src/wbgt_kiosk_en.py --demo
```

### GUI Mode (Experimental)
```bash
python src/wbgt_kiosk_en.py --gui
```

## 📊 WBGT Warning Levels

| WBGT Range | Level | Color | Description |
|------------|-------|-------|-------------|
| < 21°C | Safe | Blue | Heat stroke risk is usually low |
| 21-24°C | Caution | Green | Generally low risk, danger during intense activity |
| 25-27°C | Warning | Yellow | Take regular rest during exercise |
| 28-30°C | Severe Warning | Orange | Avoid sun, use air conditioning |
| ≥ 31°C | Dangerous | Red | Avoid going outside |

## 🔧 Advanced Setup

### Virtual Environment (Recommended)
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r setup/requirements.txt

# Run application
python src/wbgt_kiosk_en.py --demo
```

### Autostart Configuration

#### Linux (systemd)
1. Create service file:
```bash
sudo nano /etc/systemd/system/wbgt-kiosk-en.service
```

2. Add configuration:
```ini
[Unit]
Description=WBGT Heat Stroke Warning Kiosk (English)
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wbgt
ExecStart=/usr/bin/python3 /home/pi/wbgt/src/wbgt_kiosk_en.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable service:
```bash
sudo systemctl enable wbgt-kiosk-en.service
sudo systemctl start wbgt-kiosk-en.service
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "When the computer starts"
4. Set action: Start program
5. Program: `python`
6. Arguments: `src/wbgt_kiosk_en.py`
7. Start in: `[installation directory]`

## 📱 Display Examples

### Terminal Mode Output
```
==============================================================================
           🌡️  WBGT Heat Stroke Warning Kiosk (Multi-Location)  🌡️
==============================================================================
Current Time: 2024-06-23 15:30:25
Monitoring Locations: Tokyo / Yokohama

🌤️  Tokyo - Current Weather Information
--------------------------------------------------
Temperature:  32°C
Humidity:     65%
Weather:      Partly Cloudy
Feels Like:   34°C

🌡️  Tokyo - WBGT Index (Heat Stroke Index)
--------------------------------------------------
WBGT Index: 28.5°C (Severe Warning)
Data Source: Official Environment Ministry Data

📋 Advice:
   Avoid sun when outside, use air conditioning appropriately indoors

Level: ⚠️⚠️ SEVERE WARNING ⚠️⚠️

🚨 Tokyo - Heat Stroke Warning Alert
--------------------------------------------------
Today:    Heat Stroke Alert
Tomorrow: No Alert
```

## 🔧 SSL Certificate Issues and CSV Mode

### Handling SSL Certificate Errors

When SSL certificate issues occur in corporate environments, you can use CSV mode to operate with offline data.

#### CSV Mode Usage

**1. Download CSV data only:**
```bash
./scripts/run_with_csv.sh --download-only
```

**2. Run system with CSV data (Japanese version):**
```bash
./scripts/run_with_csv.sh
```

**3. Run system with CSV data (English version):**
```bash
./scripts/run_with_csv.sh --english
```

**4. Use existing CSV data (no download):**
```bash
./scripts/run_with_csv.sh --run-only
```

#### Individual Data Downloads
```bash
# JMA weather data only
./scripts/download_jma_data.sh

# Environment Ministry WBGT data only
./scripts/download_wbgt_data.sh

# Download all data
./scripts/download_all_data.sh
```

#### Testing CSV Mode
```bash
python3 test_csv_mode.py
```

For detailed instructions, see [CSV_USAGE_README.md](CSV_USAGE_README.md).

## 🛠️ Troubleshooting

### Common Issues

**ImportError: No module named 'requests'**
```bash
pip install requests
```

**Config file not found**
```bash
# JSON config (recommended)
cp setup/config.json setup/config.json.bak
nano setup/config.json

# Python config (legacy)
cp setup/config_en.sample.py setup/config_en.py
```

**SSL Certificate errors**
Use CSV mode to bypass SSL issues:
```bash
./scripts/download_all_data.sh           # Download data
./scripts/run_with_csv.sh --english      # Run English version with CSV
./scripts/run_with_csv.sh --run-only     # Use existing CSV data
```

**GUI not available**
- Install tkinter: `sudo apt-get install python3-tk` (Linux)
- Reinstall Python with tkinter support (Windows/macOS)

**Network connection errors**
- Check internet connection
- Verify firewall settings
- Check proxy configuration (corporate environments)
- Try CSV mode for offline operation

### Logging

Application logs are saved to `wbgt_kiosk_en.log`:
```bash
tail -f wbgt_kiosk_en.log        # View real-time application logs
tail -f logs/master_download.log # View CSV download logs
```

## 🔄 Data Sources

1. **Primary**: Japan Ministry of the Environment WBGT Data Service
   - Official WBGT measurements
   - Heat stroke warning alerts
   - Service period: Late April to late October

2. **Fallback**: Japan Meteorological Agency (JMA) API
   - Weather forecast data
   - Calculated WBGT estimates
   - Available year-round

## 📞 Support

### Log Files
- Application: `wbgt_kiosk_en.log`
- Service (Linux): `journalctl -u wbgt-kiosk-en.service`

### Configuration Tools
```bash
# Check current settings
python3 scripts/get_config.py locations
python3 scripts/get_config.py area_codes
python3 scripts/get_config.py prefectures

# Test CSV mode
python3 test_csv_mode.py
```

### Reset Configuration
```bash
# JSON config
cp setup/config.json setup/config.json.bak

# Python config
cp setup/config_en.sample.py setup/config_en.py
```

## 🔗 Related Documentation

- [CSV_USAGE_README.md](CSV_USAGE_README.md) - Detailed CSV mode guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide  
- [SSL_README.md](SSL_README.md) - SSL certificate troubleshooting
- [LANGUAGE_SWITCHING.md](LANGUAGE_SWITCHING.md) - Multi-language support
- [WINDOWS_README.md](WINDOWS_README.md) - Windows-specific guide

## 🌍 Localization

This is the English version. For Japanese version:
- `src/wbgt_kiosk.py` (Japanese main application)
- `setup/config.json` or `setup/config.py` (Configuration)
- `README.md` (Japanese documentation)

## 🤝 Contributing & Support

- Bug reports and feature requests: Please use Issues
- Pull requests are welcome
- Security issues: Please contact privately

## 📄 License

MIT License - Open source project for heat stroke prevention and public safety.

## 🏷️ Version

**Version 2.0.0** - July 2025
- JSON configuration file support
- CSV download script integration with config
- Multi-location monitoring support  
- Backward compatibility maintained

---

**⚠️ Important**: This system is for informational purposes. Always follow official heat stroke warnings and seek medical attention if experiencing heat-related symptoms.