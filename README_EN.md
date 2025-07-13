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

Edit `setup/config_en.py` to customize your setup:

```python
LOCATIONS = [
    {
        'name': 'Tokyo',                      # Display name
        'area_code': '130000',                # JMA area code
        'prefecture': 'Tokyo',                # Prefecture for Environment Ministry API
        'wbgt_location_code': '44132'         # Environment Ministry WBGT code
    }
]

UPDATE_INTERVAL_MINUTES = 5  # Update frequency
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
cp config_en.sample.py config_en.py
```

**SSL Certificate errors**
Use CSV mode to bypass SSL issues:
```bash
./scripts/run_with_csv.sh --download-only  # Download data
./scripts/run_with_csv.sh --run-only       # Run with CSV data
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

### Reset Configuration
```bash
cp setup/config_en.sample.py setup/config_en.py
```

### Update Dependencies
```bash
pip install -r setup/requirements.txt --upgrade
```

## 🌍 Localization

This is the English version of the WBGT Heat Stroke Warning Kiosk. For the Japanese version, use:
- `src/wbgt_kiosk.py` (Japanese main application)
- `setup/config.py` (Japanese configuration)
- `README.md` (Japanese documentation)

## 📄 License

This project is designed for heat stroke prevention and public safety purposes.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- Add appropriate error handling
- Test with both JMA and Environment Ministry data sources
- Update documentation for any new features

---

**⚠️ Important**: This system is for informational purposes. Always follow official heat stroke warnings and seek medical attention if experiencing heat-related symptoms.