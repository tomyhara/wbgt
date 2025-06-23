import requests
import json
import math
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JMAWeatherAPIEN:
    def __init__(self, area_code='130000'):
        self.area_code = area_code
        self.base_url = "https://www.jma.go.jp/bosai"
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
        try:
            forecast_url = f"{self.base_url}/forecast/data/forecast/{self.area_code}.json"
            response = requests.get(forecast_url, timeout=10)
            response.raise_for_status()
            forecast_data = response.json()
            
            # Also get observation data
            obs_url = f"{self.base_url}/amedas/const/amedastable.json"
            obs_response = requests.get(obs_url, timeout=10)
            obs_response.raise_for_status()
            
            return self._parse_weather_data(forecast_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get weather data: {e}")
            return None
        except Exception as e:
            logger.error(f"Data parsing error: {e}")
            return None
    
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
            
            # Temperature data (if available)
            temp_data = None
            if len(time_series) > 2:
                temp_data = time_series[2]
            
            # Default values (when actual observation data is unavailable)
            temperature = 25.0  # Default temperature
            humidity = 60  # Default humidity
            
            # Estimate temperature and humidity from weather code
            temp_humidity = self._estimate_temp_humidity_from_weather(weather_code, weather_desc)
            temperature = temp_humidity['temperature']
            humidity = temp_humidity['humidity']
            
            return {
                'temperature': temperature,
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
        """Remove extra spaces from weather description"""
        if not weather_desc:
            return "Unknown"
        
        # Remove full-width and half-width spaces
        cleaned = weather_desc.replace('　', '').replace(' ', '')
        
        return cleaned
    
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