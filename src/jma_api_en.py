import requests
import json
import math
import os
import sys
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JMAWeatherAPIEN:
    def __init__(self, area_code='130000'):
        self.area_code = area_code
        self.base_url = "https://www.jma.go.jp/bosai"
        
        # SSL設定の読み込み（Windows企業環境対応）
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config import SSL_VERIFY, SSL_CERT_PATH
            self.ssl_verify = SSL_VERIFY
            self.ssl_cert_path = SSL_CERT_PATH
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                logger.warning("SSL証明書検証が無効化されています（企業環境向け設定）")
        except ImportError:
            self.ssl_verify = True
            self.ssl_cert_path = None
        self.area_codes = {
            'Sapporo': '016000',
            'Aomori': '020000', 
            'Morioka': '030000',
            'Sendai': '040000',
            'Akita': '050000',
            'Yamagata': '060000',
            'Fukushima': '070000',
            'Mito': '080000',
            'Utsunomiya': '090000',
            'Maebashi': '100000',
            'Saitama': '110000',
            'Chiba': '120000',
            'Tokyo': '130000',
            'Yokohama': '140000',
            'Niigata': '150000',
            'Toyama': '160000',
            'Kanazawa': '170000',
            'Fukui': '180000',
            'Kofu': '190000',
            'Nagano': '200000',
            'Gifu': '210000',
            'Shizuoka': '220000',
            'Nagoya': '230000',
            'Tsu': '240000',
            'Otsu': '250000',
            'Kyoto': '260000',
            'Osaka': '270000',
            'Kobe': '280000',
            'Nara': '290000',
            'Wakayama': '300000',
            'Tottori': '310000',
            'Matsue': '320000',
            'Okayama': '330000',
            'Hiroshima': '340000',
            'Yamaguchi': '350000',
            'Tokushima': '360000',
            'Takamatsu': '370000',
            'Matsuyama': '380000',
            'Kochi': '390000',
            'Fukuoka': '400000',
            'Saga': '410000',
            'Nagasaki': '420000',
            'Kumamoto': '430000',
            'Oita': '440000',
            'Miyazaki': '450000',
            'Kagoshima': '460100',
            'Naha': '471000'
        }
    
    def get_current_weather(self):
        """Get current weather data"""
        # Check for forced CSV mode
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("Forced CSV mode enabled: Attempting to read data from CSV file...")
            return self._get_weather_from_csv()
        
        try:
            forecast_url = f"{self.base_url}/forecast/data/forecast/{self.area_code}.json"
            response = requests.get(forecast_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            forecast_data = response.json()
            
            # Also get observation data
            obs_url = f"{self.base_url}/amedas/const/amedastable.json"
            obs_response = requests.get(obs_url, timeout=10, verify=self.ssl_verify)
            obs_response.raise_for_status()
            
            return self._parse_weather_data(forecast_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get weather data: {e}")
            logger.info("Attempting to read data from CSV file...")
            return self._get_weather_from_csv()
        except Exception as e:
            logger.error(f"Data parsing error: {e}")
            logger.info("Attempting to read data from CSV file...")
            return self._get_weather_from_csv()
    
    def _parse_weather_data(self, forecast_data):
        """Parse forecast data"""
        try:
            # Get basic information
            publishing_office = forecast_data[0]['publishingOffice']
            report_datetime = forecast_data[0]['reportDatetime']
            
            # Get today's forecast
            time_series = forecast_data[0]['timeSeries']
            
            # Weather forecast data
            weather_data = time_series[0]
            areas = weather_data['areas'][0]
            
            # Today's weather
            weather_code = areas['weatherCodes'][0] if areas.get('weatherCodes') else '100'
            weather_desc_raw = areas['weathers'][0] if areas.get('weathers') else 'Clear'
            weather_desc = self._simplify_weather_description(weather_desc_raw)
            
            # Get temperature data
            current_temp = None
            forecast_high = None
            forecast_low = None
            
            # Get temperature from JMA forecast data
            for ts in time_series:
                areas_temp = ts.get('areas', [])
                if areas_temp and 'temps' in areas_temp[0]:
                    # Temperature forecast data is included
                    temps = areas_temp[0].get('temps', [])
                    time_defines = ts.get('timeDefines', [])
                    
                    # temps array structure: [today_high, today_high(duplicate), tomorrow_low, tomorrow_high]
                    # Main logic: directly get from array
                    if len(temps) >= 1 and temps[0]:
                        forecast_high = int(temps[0])  # Today's high temperature
                        logger.info(f"Got today's high temperature: {forecast_high}°C")
                    
                    if len(temps) >= 3 and temps[2]:
                        forecast_low = int(temps[2])   # Use tomorrow's low as today's low
                        logger.info(f"Got today's low temperature: {forecast_low}°C")
                    elif len(temps) >= 2 and temps[1]:
                        forecast_low = int(temps[1])   # Fallback
                        logger.info(f"Got today's low temperature (fallback): {forecast_low}°C")
                    
                    # Break after finding first temps data
                    break
            
            # Default values for current and forecast temperatures
            if not current_temp:
                # Try to get current temperature from AMeDAS real-time data
                current_temp = self._get_current_temperature_from_amedas()
                
                if not current_temp:
                    # Fall back to estimation from weather code if AMeDAS data unavailable
                    temp_humidity = self._estimate_temp_humidity_from_weather(weather_code, weather_desc)
                    current_temp = temp_humidity['temperature']
                    humidity = temp_humidity['humidity']
                else:
                    humidity = 60  # Default humidity
            else:
                humidity = 60  # Default humidity
            
            # Only estimate if forecast temperatures cannot be obtained
            if not forecast_high:
                forecast_high = current_temp + 3
                logger.warning(f"Using estimated high temperature as forecast data unavailable: {forecast_high}°C")
            if not forecast_low:
                forecast_low = current_temp - 2
                logger.warning(f"Using estimated low temperature as forecast data unavailable: {forecast_low}°C")
            
            return {
                'temperature': current_temp,
                'forecast_high': forecast_high,
                'forecast_low': forecast_low,
                'humidity': humidity,
                'weather_description': weather_desc,
                'weather_code': weather_code,
                'pressure': 1013,  # Standard pressure
                'wind_speed': 0,
                'publishing_office': publishing_office,
                'report_datetime': report_datetime
            }
            
        except Exception as e:
            logger.error(f"Failed to parse weather data: {e}")
            return None
    
    def _estimate_temp_humidity_from_weather(self, weather_code, weather_desc):
        """Estimate temperature and humidity from weather code"""
        # Consider current season
        month = datetime.now().month
        
        # Base temperature by season
        if month in [12, 1, 2]:  # Winter
            base_temp = 8
        elif month in [3, 4, 5]:  # Spring
            base_temp = 18
        elif month in [6, 7, 8]:  # Summer
            base_temp = 28
        else:  # Autumn
            base_temp = 20
        
        # Adjustment by weather
        if 'clear' in weather_desc.lower() or 'sunny' in weather_desc.lower():
            temp_adj = 2
            humidity = 50
        elif 'cloud' in weather_desc.lower():
            temp_adj = 0
            humidity = 65
        elif 'rain' in weather_desc.lower():
            temp_adj = -3
            humidity = 85
        elif 'snow' in weather_desc.lower():
            temp_adj = -5
            humidity = 80
        else:
            temp_adj = 0
            humidity = 60
        
        return {
            'temperature': max(base_temp + temp_adj, 0),
            'humidity': humidity
        }
    
    def _simplify_weather_description(self, weather_desc):
        """Simplify weather description"""
        if not weather_desc:
            return "Unknown"
        
        # Remove full-width and half-width spaces
        cleaned = weather_desc.replace('　', '').replace(' ', '')
        
        # Simplify long descriptions
        if '晴' in cleaned:
            if '時々' in cleaned or 'のち' in cleaned:
                return "Partly Cloudy" if '曇' in cleaned else "Sunny"
            return "Sunny"
        elif '曇' in cleaned:
            if '雨' in cleaned or '雷' in cleaned:
                return "Cloudy/Rain"
            elif '晴' in cleaned:
                return "Partly Sunny"
            return "Cloudy"
        elif '雨' in cleaned:
            if '雷' in cleaned:
                return "Rain/Thunder"
            elif '雪' in cleaned:
                return "Rain/Snow"
            return "Rain"
        elif '雪' in cleaned:
            if '雨' in cleaned:
                return "Snow/Rain"
            return "Snow"
        else:
            # For other cases, limit to first 15 characters
            return cleaned[:15]
    
    def _get_current_temperature_from_amedas(self):
        """Get current temperature from JMA overview_forecast API"""
        try:
            # overview_forecast endpoint URL
            overview_url = f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{self.area_code}.json"
            
            response = requests.get(overview_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            overview_data = response.json()
            
            # Try to get current temperature data
            if 'targetArea' in overview_data:
                target_area = overview_data['targetArea']
                # Extract temperature information from text
                text = overview_data.get('text', '')
                
                # Look for patterns like "current temperature is X degrees"
                import re
                temp_patterns = [
                    r'current.*?temperature.*?(\d+(?:\.\d+)?).*?degree',
                    r'temperature.*?(\d+(?:\.\d+)?).*?degree',
                    r'(\d+(?:\.\d+)?).*?degree.*?temperature',
                    r'現在.*?気温.*?(\d+(?:\.\d+)?)度',  # Japanese patterns as fallback
                    r'気温.*?(\d+(?:\.\d+)?)度',
                    r'(\d+(?:\.\d+)?)度.*?気温'
                ]
                
                for pattern in temp_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        temp = float(match.group(1))
                        logger.info(f"overview_forecast temperature acquired: {temp}°C (area: {target_area})")
                        return temp
                
                logger.debug(f"overview_forecast text: {text}")
            
            # Fall back to traditional AMeDAS method if overview_forecast doesn't work
            return self._get_current_temperature_from_amedas_fallback()
            
        except Exception as e:
            logger.error(f"overview_forecast temperature acquisition error: {e}")
            # Fall back to traditional method on error
            return self._get_current_temperature_from_amedas_fallback()
    
    def _get_current_temperature_from_amedas_fallback(self):
        """Get current temperature from AMeDAS real-time data (fallback)"""
        try:
            from datetime import datetime, timedelta
            import json
            
            # Get data from 1 hour ago (considering AMeDAS data update frequency)
            now = datetime.now()
            target_time = now - timedelta(hours=1)
            date_str = target_time.strftime('%Y%m%d')
            hour_str = target_time.strftime('%H')
            
            # AMeDAS real-time data URL
            amedas_url = f"https://www.jma.go.jp/bosai/amedas/data/map/{date_str}{hour_str}0000.json"
            
            response = requests.get(amedas_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            amedas_data = response.json()
            
            # Search for AMeDAS stations corresponding to area codes
            # Yokohama: 46106, Chiba(Choshi): 45148, etc.
            target_stations = {
                '140000': ['46106', '46078'],  # Kanagawa: Yokohama, Odawara
                '120000': ['45148', '45056']   # Chiba: Choshi, Kisarazu
            }
            
            stations_to_check = target_stations.get(self.area_code, [])
            
            # Search data for relevant stations
            for station_id in stations_to_check:
                if station_id in amedas_data:
                    station_data = amedas_data[station_id]
                    if 'temp' in station_data and station_data['temp'][0] is not None:
                        temp = float(station_data['temp'][0])
                        logger.info(f"AMeDAS temperature acquired: {temp}°C (station: {station_id})")
                        return temp
            
            # Try major stations in Tokyo metropolitan area as fallback
            fallback_stations = ['44132', '44136', '46106', '45148']  # Tokyo, Nerima, Yokohama, Choshi
            for station_id in fallback_stations:
                if station_id in amedas_data:
                    station_data = amedas_data[station_id]
                    if 'temp' in station_data and station_data['temp'][0] is not None:
                        temp = float(station_data['temp'][0])
                        logger.info(f"AMeDAS temperature acquired (fallback): {temp}°C (station: {station_id})")
                        return temp
            
            logger.warning("Could not acquire temperature from AMeDAS real-time data")
            return None
            
        except Exception as e:
            logger.error(f"AMeDAS real-time data acquisition error: {e}")
            return None
        
        # Simplify long descriptions
        if '晴' in cleaned:
            if '時々' in cleaned or 'のち' in cleaned:
                return "Partly Cloudy" if '曇' in cleaned else "Sunny"
            return "Sunny"
        elif '曇' in cleaned:
            if '雨' in cleaned or '雷' in cleaned:
                return "Cloudy/Rain"
            elif '晴' in cleaned:
                return "Partly Sunny"
            return "Cloudy"
        elif '雨' in cleaned:
            if '雷' in cleaned:
                return "Rain/Thunder"
            elif '雪' in cleaned:
                return "Rain/Snow"
            return "Rain"
        elif '雪' in cleaned:
            if '雨' in cleaned:
                return "Snow/Rain"
            return "Snow"
        else:
            # For other cases, limit to first 15 characters
            return cleaned[:15]
    
    def calculate_wbgt(self, temp, humidity):
        """Calculate WBGT index"""
        # Calculate wet bulb temperature
        temp_k = temp + 273.15
        es = 6.112 * math.exp(17.67 * temp / (temp + 243.5))
        e = es * humidity / 100
        td = 243.5 * math.log(e / 6.112) / (17.67 - math.log(e / 6.112))
        
        # WBGT calculation for outdoors (without solar radiation)
        wbgt = 0.7 * td + 0.2 * temp + 3.0
        
        return round(wbgt, 1)
    
    def get_wbgt_level(self, wbgt):
        """Determine warning level from WBGT index"""
        if wbgt < 21:
            return "Safe", "green", "Moderate exercise is possible"
        elif wbgt < 25:
            return "Caution", "yellow", "Active hydration required"
        elif wbgt < 28:
            return "Warning", "orange", "Avoid intense exercise"
        elif wbgt < 31:
            return "Severe Warning", "red", "Exercise should be cancelled"
        else:
            return "Extremely Dangerous", "darkred", "Avoid going outside"
    
    def get_weather_data(self):
        """Get weather data and WBGT index"""
        weather_data = self.get_current_weather()
        if not weather_data:
            return None
        
        temp = weather_data['temperature']
        humidity = weather_data['humidity']
        wbgt = self.calculate_wbgt(temp, humidity)
        level, color, advice = self.get_wbgt_level(wbgt)
        
        return {
            'temperature': round(temp, 1),
            'forecast_high': weather_data['forecast_high'],
            'forecast_low': weather_data['forecast_low'],
            'humidity': humidity,
            'weather_description': weather_data['weather_description'],
            'weather_code': weather_data['weather_code'],
            'feels_like': round(temp + 2, 1),  # Simple calculation for feels like temperature
            'pressure': weather_data['pressure'],
            'wind_speed': weather_data['wind_speed'],
            'wbgt': wbgt,
            'wbgt_level': level,
            'wbgt_color': color,
            'wbgt_advice': advice,
            'publishing_office': weather_data['publishing_office'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _get_weather_from_csv(self):
        """Get weather data from CSV file (fallback when API access fails)"""
        try:
            # Build JSON file path
            script_dir = os.path.dirname(os.path.dirname(__file__))
            json_file = os.path.join(script_dir, 'data', 'csv', f'jma_forecast_{self.area_code}.json')
            
            if not os.path.exists(json_file):
                logger.warning(f"JMA JSON file not found: {json_file}")
                return None
            
            # Check file modification time (whether within 24 hours)
            file_mtime = os.path.getmtime(json_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24 hours
                logger.warning(f"JMA JSON file is too old ({(current_time - file_mtime) / 3600:.1f} hours ago)")
                return None
            
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                forecast_data = json.load(f)
            
            logger.info(f"Successfully read data from JSON file: {json_file}")
            return self._parse_weather_data(forecast_data)
            
        except Exception as e:
            logger.error(f"Error reading data from JSON file: {e}")
            return None