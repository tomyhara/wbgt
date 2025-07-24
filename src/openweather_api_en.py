#!/usr/bin/env python3
"""
OpenWeatherMap API wrapper for WBGT Kiosk (English Version)
Weather data retrieval using OpenWeatherMap API
"""

import requests
import json
import math
import os
from datetime import datetime
import logging

# Import offline parser for SSL/connectivity issues
try:
    from openweather_csv_parser import OpenWeatherOfflineAPI
    OFFLINE_PARSER_AVAILABLE = True
except ImportError:
    OFFLINE_PARSER_AVAILABLE = False

logger = logging.getLogger(__name__)

class OpenWeatherAPIEN:
    def __init__(self, api_key=None, city_name=None, lat=None, lon=None):
        """
        Initialize OpenWeatherMap API client
        
        Args:
            api_key (str): OpenWeatherMap API key
            city_name (str): City name (e.g., "Yokohama,JP")
            lat (float): Latitude (alternative to city_name)
            lon (float): Longitude (alternative to city_name)
        """
        self.api_key = api_key
        self.city_name = city_name
        self.lat = lat
        self.lon = lon
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # SSL configuration for corporate environments
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config_loader import load_config
            config = load_config()
            ssl_config = config.get('ssl', {})
            self.ssl_verify = ssl_config.get('verify', True)
            self.ssl_cert_path = ssl_config.get('cert_path', None)
            
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except ImportError:
            self.ssl_verify = True
            self.ssl_cert_path = None
        
        # Load API key from config if not provided
        if not self.api_key:
            try:
                config = load_config()
                self.api_key = config.get('openweather_api_key', '')
            except:
                logger.warning("OpenWeatherMap API key not found in configuration")
        
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is required")
    
    def _make_request(self, endpoint, params=None):
        """Make HTTP request to OpenWeatherMap API"""
        if params is None:
            params = {}
        
        # Add API key and units
        params['appid'] = self.api_key
        params['units'] = 'metric'  # Celsius temperature
        params['lang'] = 'en'  # English language
        
        # Add location parameters
        if self.city_name:
            params['q'] = self.city_name
        elif self.lat and self.lon:
            params['lat'] = self.lat
            params['lon'] = self.lon
        else:
            raise ValueError("Either city_name or lat/lon must be specified")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # Apply SSL configuration
            if self.ssl_cert_path:
                response = requests.get(url, params=params, verify=self.ssl_cert_path, timeout=10)
            else:
                response = requests.get(url, params=params, verify=self.ssl_verify, timeout=10)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenWeatherMap API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenWeatherMap API response: {e}")
            return None
    
    def get_current_weather(self):
        """Get current weather data"""
        return self._make_request('weather')
    
    def get_forecast(self, cnt=5):
        """
        Get weather forecast
        
        Args:
            cnt (int): Number of forecast periods (max 40 for 5-day forecast)
        """
        return self._make_request('forecast', {'cnt': cnt})
    
    def get_weather_data(self):
        """
        Get formatted weather data compatible with existing WBGT system
        Returns data in the same format as JMA API for compatibility
        """
        try:
            # Get current weather
            current_data = self.get_current_weather()
            if not current_data:
                logger.error("Failed to get current weather data from OpenWeatherMap")
                return None
            
            # Get forecast for min/max temperatures
            forecast_data = self.get_forecast(cnt=8)  # Next 24 hours (3-hour intervals)
            
            # Extract current weather information
            main = current_data.get('main', {})
            weather = current_data.get('weather', [{}])[0]
            wind = current_data.get('wind', {})
            
            # Calculate forecast high/low temperatures
            forecast_temps = []
            if forecast_data and 'list' in forecast_data:
                for item in forecast_data['list']:
                    forecast_temps.append(item['main']['temp'])
            
            if forecast_temps:
                forecast_high = max(forecast_temps)
                forecast_low = min(forecast_temps)
            else:
                # Fallback to current temperature
                forecast_high = main.get('temp', 0)
                forecast_low = main.get('temp', 0)
            
            # Format weather data to match JMA API structure
            weather_data = {
                'temperature': round(main.get('temp', 0), 1),
                'humidity': main.get('humidity', 0),
                'weather_description': weather.get('description', 'Unknown'),
                'feels_like': round(main.get('feels_like', 0), 1),
                'wind_speed': wind.get('speed', 0),
                'pressure': main.get('pressure', 0),
                'visibility': current_data.get('visibility', 0) / 1000 if current_data.get('visibility') else 0,  # Convert m to km
                'uv_index': 0,  # Will be populated by UV API if available
                'forecast_high': round(forecast_high, 1),
                'forecast_low': round(forecast_low, 1),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'OpenWeatherMap',
                
                # Additional OpenWeatherMap specific data
                'weather_icon': weather.get('icon', ''),
                'weather_main': weather.get('main', ''),
                'clouds': current_data.get('clouds', {}).get('all', 0),
                'sunrise': datetime.fromtimestamp(current_data.get('sys', {}).get('sunrise', 0)).strftime('%H:%M') if current_data.get('sys', {}).get('sunrise') else '',
                'sunset': datetime.fromtimestamp(current_data.get('sys', {}).get('sunset', 0)).strftime('%H:%M') if current_data.get('sys', {}).get('sunset') else '',
            }
            
            logger.info(f"Successfully retrieved weather data from OpenWeatherMap for {self.city_name or f'{self.lat},{self.lon}'}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap weather data: {e}")
            return None
    
    def get_uv_index(self):
        """
        Get UV Index data (requires separate API call)
        Note: OpenWeatherMap UV Index API may require a different subscription
        """
        if not (self.lat and self.lon):
            logger.warning("UV Index requires lat/lon coordinates")
            return None
        
        try:
            # UV Index endpoint (note: this might require a different API key/plan)
            uv_data = self._make_request('uvi', {})
            if uv_data:
                return uv_data.get('value', 0)
        except:
            logger.warning("UV Index data not available")
        
        return 0
    
    @staticmethod
    def get_location_coords(location_name):
        """
        Get coordinates for a location name
        Helper method for converting location names to coordinates
        """
        # Mapping for Japanese location names to coordinates
        location_coords = {
            'Yokohama': (35.4478, 139.6425),
            'Tokyo': (35.6762, 139.6503),
            'Chiba': (35.6074, 140.1065),
            'Choshi': (35.7347, 140.8317),
            'Sapporo': (43.0642, 141.3469),
            'Sendai': (38.2682, 140.8694),
            'Osaka': (34.6937, 135.5023),
            'Nagoya': (35.1815, 136.9066),
            'Fukuoka': (33.5904, 130.4017),
            # Japanese names as well
            '横浜': (35.4478, 139.6425),
            '東京': (35.6762, 139.6503),
            '千葉': (35.6074, 140.1065),
            '銚子': (35.7347, 140.8317),
            '札幌': (43.0642, 141.3469),
            '仙台': (38.2682, 140.8694),
            '大阪': (34.6937, 135.5023),
            '名古屋': (35.1815, 136.9066),
            '福岡': (33.5904, 130.4017),
        }
        
        return location_coords.get(location_name, None)
    
    @classmethod
    def create_from_location_name(cls, location_name, api_key=None):
        """
        Create OpenWeatherAPIEN instance from location name
        
        Args:
            location_name (str): Location name (Japanese or English)
            api_key (str): OpenWeatherMap API key
        """
        coords = cls.get_location_coords(location_name)
        if coords:
            lat, lon = coords
            return cls(api_key=api_key, lat=lat, lon=lon)
        else:
            # Fallback to city name search
            city_query = f"{location_name},JP"
            return cls(api_key=api_key, city_name=city_query)


# Backward compatibility wrapper
class OpenWeatherMapAPIEN(OpenWeatherAPIEN):
    """Alias for backward compatibility"""
    pass