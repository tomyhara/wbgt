#!/usr/bin/env python3
"""
Test script to verify CSV-only mode functionality
"""

import os
import sys
from datetime import datetime

# Set up path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, 'src'))
sys.path.append(os.path.join(script_dir, 'setup'))

# Set forced CSV mode
os.environ['FORCE_CSV_MODE'] = '1'

def test_env_wbgt_api():
    """Test Environment Ministry WBGT API with CSV data"""
    print("=== Testing Environment Ministry WBGT API (CSV Mode) ===")
    
    try:
        from env_wbgt_api import EnvWBGTAPI
        
        # Configure location (matching setup/config.py format)
        location = {
            'name': 'Test Location',
            'prefecture': '神奈川県',
            'wbgt_location_code': '45106'  # Kanagawa code
        }
        
        api = EnvWBGTAPI()
        
        # Test forecast data
        print("Testing forecast data...")
        forecast_data = api.get_wbgt_forecast_data(location)
        if forecast_data:
            print(f"✅ Forecast data retrieved: WBGT={forecast_data.get('wbgt_value')}, Source={forecast_data.get('source')}")
        else:
            print("❌ Failed to retrieve forecast data")
        
        # Test current data
        print("Testing current data...")
        current_data = api.get_wbgt_current_data(location)
        if current_data:
            print(f"✅ Current data retrieved: WBGT={current_data.get('wbgt_value')}, Source={current_data.get('source')}")
        else:
            print("❌ Failed to retrieve current data")
        
        # Test alert data
        print("Testing alert data...")
        alert_data = api.get_alert_data(location)
        if alert_data:
            alerts = alert_data.get('alerts', {})
            today_status = alerts.get('today', {}).get('status', 'Unknown')
            print(f"✅ Alert data retrieved: Today={today_status}, Source={alert_data.get('source')}")
        else:
            print("❌ Failed to retrieve alert data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing WBGT API: {e}")
        return False

def test_jma_api():
    """Test JMA Weather API with CSV data"""
    print("\n=== Testing JMA Weather API (CSV Mode) ===")
    
    try:
        from jma_api import JMAWeatherAPI
        
        api = JMAWeatherAPI(area_code='130000')  # Tokyo
        
        # Test weather data
        print("Testing weather data...")
        weather_data = api.get_weather_data()
        if weather_data:
            temp = weather_data.get('temperature')
            desc = weather_data.get('weather_description')
            wbgt = weather_data.get('wbgt')
            print(f"✅ Weather data retrieved: Temp={temp}°C, Weather={desc}, WBGT={wbgt}")
        else:
            print("❌ Failed to retrieve weather data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing JMA API: {e}")
        return False

def main():
    """Main test function"""
    print(f"CSV Mode Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"FORCE_CSV_MODE = {os.environ.get('FORCE_CSV_MODE')}")
    
    # Check if CSV files exist
    csv_dir = os.path.join(script_dir, 'data', 'csv')
    if not os.path.exists(csv_dir):
        print(f"❌ CSV directory not found: {csv_dir}")
        print("Please run: ./scripts/run_with_csv.sh --download-only")
        return False
    
    csv_files = os.listdir(csv_dir)
    print(f"Found {len(csv_files)} CSV/JSON files in {csv_dir}")
    
    # Run tests
    success_count = 0
    total_tests = 2
    
    if test_env_wbgt_api():
        success_count += 1
    
    if test_jma_api():
        success_count += 1
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Passed: {success_count}/{total_tests} tests")
    
    if success_count == total_tests:
        print("🎉 All tests passed! CSV mode is working correctly.")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)