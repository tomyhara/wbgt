#!/usr/bin/env python3
"""
OpenWeatherMap CSV/JSON Data Parser for Offline Mode
オフラインモード用OpenWeatherMapデータパーサー
"""

import json
import os
import glob
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class OpenWeatherCSVParser:
    def __init__(self, data_dir=None):
        """
        Initialize OpenWeatherMap CSV parser
        
        Args:
            data_dir (str): Directory containing downloaded OpenWeatherMap data
        """
        if data_dir is None:
            # Default to project data directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            data_dir = os.path.join(project_root, 'data', 'csv', 'openweather')
        
        self.data_dir = data_dir
        self.logger = logger
    
    def get_latest_data_file(self, location_name, data_type='current'):
        """
        Get the latest data file for a location
        
        Args:
            location_name (str): Location name
            data_type (str): 'current' or 'forecast'
        
        Returns:
            str: Path to the latest data file, or None if not found
        """
        # Try latest symlink first
        latest_file = os.path.join(self.data_dir, f"{location_name}_{data_type}_latest.json")
        if os.path.exists(latest_file) and os.path.islink(latest_file):
            actual_file = os.path.join(self.data_dir, os.readlink(latest_file))
            if os.path.exists(actual_file):
                return actual_file
        
        # Fallback to finding latest timestamped file
        pattern = os.path.join(self.data_dir, f"{location_name}_{data_type}_*.json")
        files = glob.glob(pattern)
        
        if not files:
            return None
        
        # Sort by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]
    
    def load_json_data(self, file_path):
        """
        Load JSON data from file
        
        Args:
            file_path (str): Path to JSON file
        
        Returns:
            dict: Parsed JSON data, or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            self.logger.error(f"Failed to load JSON data from {file_path}: {e}")
            return None
    
    def parse_current_weather(self, location_name):
        """
        Parse current weather data for a location
        
        Args:
            location_name (str): Location name
        
        Returns:
            dict: Formatted weather data compatible with OpenWeatherAPI
        """
        file_path = self.get_latest_data_file(location_name, 'current')
        if not file_path:
            self.logger.warning(f"No current weather data found for {location_name}")
            return None
        
        data = self.load_json_data(file_path)
        if not data:
            return None
        
        try:
            # Check if data is recent (within last 3 hours)
            file_mtime = os.path.getmtime(file_path)
            file_time = datetime.fromtimestamp(file_mtime)
            if datetime.now() - file_time > timedelta(hours=3):
                self.logger.warning(f"Weather data for {location_name} is outdated (from {file_time})")
            
            # Extract weather information
            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})
            
            # Format to match OpenWeatherAPI structure
            formatted_data = {
                'temperature': round(main.get('temp', 0), 1),
                'humidity': main.get('humidity', 0),
                'weather_description': weather.get('description', '不明'),
                'feels_like': round(main.get('feels_like', 0), 1),
                'wind_speed': wind.get('speed', 0),
                'pressure': main.get('pressure', 0),
                'visibility': data.get('visibility', 0) / 1000 if data.get('visibility') else 0,
                'timestamp': file_time.strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'OpenWeatherMap (Offline)',
                
                # Additional data
                'weather_icon': weather.get('icon', ''),
                'weather_main': weather.get('main', ''),
                'clouds': data.get('clouds', {}).get('all', 0),
                'sunrise': datetime.fromtimestamp(data.get('sys', {}).get('sunrise', 0)).strftime('%H:%M') if data.get('sys', {}).get('sunrise') else '',
                'sunset': datetime.fromtimestamp(data.get('sys', {}).get('sunset', 0)).strftime('%H:%M') if data.get('sys', {}).get('sunset') else '',
            }
            
            self.logger.info(f"Successfully parsed current weather data for {location_name}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error parsing current weather data for {location_name}: {e}")
            return None
    
    def parse_forecast_weather(self, location_name):
        """
        Parse forecast weather data for a location
        
        Args:
            location_name (str): Location name
        
        Returns:
            dict: Forecast data with high/low temperatures
        """
        file_path = self.get_latest_data_file(location_name, 'forecast')
        if not file_path:
            self.logger.warning(f"No forecast weather data found for {location_name}")
            return None
        
        data = self.load_json_data(file_path)
        if not data:
            return None
        
        try:
            forecast_list = data.get('list', [])
            if not forecast_list:
                return None
            
            # Extract temperatures from next 24 hours (8 data points at 3-hour intervals)
            temps = []
            for item in forecast_list[:8]:
                temp = item.get('main', {}).get('temp', 0)
                temps.append(temp)
            
            if temps:
                return {
                    'forecast_high': round(max(temps), 1),
                    'forecast_low': round(min(temps), 1),
                    'forecast_count': len(temps)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing forecast data for {location_name}: {e}")
            return None
    
    def get_weather_data(self, location_name):
        """
        Get complete weather data for a location (combines current and forecast)
        
        Args:
            location_name (str): Location name
        
        Returns:
            dict: Complete weather data compatible with OpenWeatherAPI.get_weather_data()
        """
        # Get current weather
        current_data = self.parse_current_weather(location_name)
        if not current_data:
            return None
        
        # Get forecast data
        forecast_data = self.parse_forecast_weather(location_name)
        
        # Merge forecast data into current data
        if forecast_data:
            current_data.update(forecast_data)
        else:
            # Use current temperature as fallback
            current_data['forecast_high'] = current_data['temperature']
            current_data['forecast_low'] = current_data['temperature']
        
        return current_data
    
    def list_available_locations(self):
        """
        List all locations with available data
        
        Returns:
            list: List of location names with available data
        """
        if not os.path.exists(self.data_dir):
            return []
        
        locations = set()
        pattern = os.path.join(self.data_dir, "*_current_*.json")
        
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            # Extract location name from filename (format: location_current_timestamp.json)
            parts = filename.split('_current_')
            if len(parts) >= 2:
                location_name = parts[0]
                locations.add(location_name)
        
        return sorted(list(locations))
    
    def get_data_freshness(self, location_name):
        """
        Check how fresh the data is for a location
        
        Args:
            location_name (str): Location name
        
        Returns:
            dict: Information about data freshness
        """
        current_file = self.get_latest_data_file(location_name, 'current')
        forecast_file = self.get_latest_data_file(location_name, 'forecast')
        
        result = {
            'location': location_name,
            'current_available': current_file is not None,
            'forecast_available': forecast_file is not None,
            'current_age_hours': None,
            'forecast_age_hours': None,
            'is_fresh': False
        }
        
        now = datetime.now()
        
        if current_file:
            current_mtime = datetime.fromtimestamp(os.path.getmtime(current_file))
            current_age = now - current_mtime
            result['current_age_hours'] = current_age.total_seconds() / 3600
            result['current_timestamp'] = current_mtime.strftime('%Y-%m-%d %H:%M:%S')
        
        if forecast_file:
            forecast_mtime = datetime.fromtimestamp(os.path.getmtime(forecast_file))
            forecast_age = now - forecast_mtime
            result['forecast_age_hours'] = forecast_age.total_seconds() / 3600
            result['forecast_timestamp'] = forecast_mtime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Consider data fresh if less than 3 hours old
        if result['current_age_hours'] is not None:
            result['is_fresh'] = result['current_age_hours'] < 3
        
        return result


# Convenience class for backward compatibility
class OpenWeatherOfflineAPI:
    """
    Offline OpenWeatherMap API that mimics the online API interface
    """
    
    def __init__(self, location_name, data_dir=None):
        self.location_name = location_name
        self.parser = OpenWeatherCSVParser(data_dir)
    
    def get_weather_data(self):
        """Get weather data (compatible with OpenWeatherAPI interface)"""
        return self.parser.get_weather_data(self.location_name)
    
    def get_current_weather(self):
        """Get current weather data"""
        return self.parser.parse_current_weather(self.location_name)
    
    def get_forecast(self):
        """Get forecast data"""
        return self.parser.parse_forecast_weather(self.location_name)
    
    @classmethod
    def create_from_location_name(cls, location_name, data_dir=None):
        """Create instance from location name (compatible with OpenWeatherAPI interface)"""
        return cls(location_name, data_dir)