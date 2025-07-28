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
            
            # Also get weekly forecast data
            weekly_data = self._parse_weekly_forecast(forecast_data)
            weather_data = self._parse_weather_data(forecast_data)
            if weather_data and weekly_data:
                weather_data['weekly_forecast'] = weekly_data
            return weather_data
            
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
                    time_defines = ts.get('timeDefines', [])
                    
                    # Find area matching the configured location name
                    target_area = None
                    # Map area codes to target location names
                    target_names = {
                        '140000': ['Yokohama', '横浜'],  # Kanagawa
                        '120000': ['Choshi', '銚子', 'Chiba', '千葉']  # Chiba
                    }
                    
                    possible_names = target_names.get(self.area_code, [])
                    
                    for area in areas_temp:
                        area_name = area['area']['name']
                        for possible_name in possible_names:
                            if possible_name in area_name or area_name in possible_name:
                                target_area = area
                                logger.info(f"Found target area: {area_name}")
                                break
                        if target_area:
                            break
                    
                    # Use first area if target area not found
                    if not target_area:
                        target_area = areas_temp[0]
                        logger.warning(f"Target area not found, using first area: {target_area['area']['name']}")
                    
                    temps = target_area.get('temps', [])
                    
                    # temps array structure: [today_high, today_high(duplicate), tomorrow_low, tomorrow_high]
                    # Main logic: directly get from array
                    if len(temps) >= 1 and temps[0]:
                        forecast_high = int(temps[0])  # Today's high temperature
                        logger.info(f"Got today's high temperature: {forecast_high}°C ({target_area['area']['name']})")
                    
                    if len(temps) >= 3 and temps[2]:
                        forecast_low = int(temps[2])   # Use tomorrow's low as today's low
                        logger.info(f"Got today's low temperature: {forecast_low}°C ({target_area['area']['name']})")
                    elif len(temps) >= 2 and temps[1]:
                        forecast_low = int(temps[1])   # Fallback
                        logger.info(f"Got today's low temperature (fallback): {forecast_low}°C ({target_area['area']['name']})")
                    
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
    
    def _parse_weekly_forecast(self, forecast_data):
        """Parse weekly forecast data (improved version)"""
        try:
            if len(forecast_data) < 2:
                logger.warning("Weekly forecast data not found")
                return None
            
            weekly_series = forecast_data[1]  # Series 1 is weekly forecast
            
            if 'timeSeries' not in weekly_series or len(weekly_series['timeSeries']) < 2:
                logger.warning("Weekly forecast time series data incomplete")
                return None
            
            # Weekly weather data (timeSeries[0])
            weather_ts = weekly_series['timeSeries'][0]
            weather_areas = weather_ts.get('areas', [])
            if not weather_areas:
                logger.warning("Weekly forecast area data not found")
                return None
            
            weather_area = weather_areas[0]
            weather_dates = weather_ts.get('timeDefines', [])
            weather_codes = weather_area.get('weatherCodes', [])
            pops = weather_area.get('pops', [])
            reliabilities = weather_area.get('reliabilities', [])
            
            logger.info(f"Weekly weather data: {weather_area['area']['name']}, days: {len(weather_dates)}")
            
            # Weekly temperature data (timeSeries[1])
            temp_ts = weekly_series['timeSeries'][1]
            temp_areas = temp_ts.get('areas', [])
            if not temp_areas:
                logger.warning("Weekly forecast temperature data not found")
                return None
            
            temp_area = temp_areas[0]
            temp_dates = temp_ts.get('timeDefines', [])
            temps_max = temp_area.get('tempsMax', [])
            temps_min = temp_area.get('tempsMin', [])
            temps_max_upper = temp_area.get('tempsMaxUpper', [])
            temps_max_lower = temp_area.get('tempsMaxLower', [])
            temps_min_upper = temp_area.get('tempsMinUpper', [])
            temps_min_lower = temp_area.get('tempsMinLower', [])
            
            logger.info(f"Weekly temperature data: {temp_area['area']['name']}, days: {len(temp_dates)}")
            
            # Map data by date for integration
            weather_data_map = {}
            for i, date_str in enumerate(weather_dates):
                if i < len(weather_codes):
                    weather_data_map[date_str] = {
                        'weather_code': weather_codes[i] if weather_codes[i] else None,
                        'pop': pops[i] if i < len(pops) and pops[i] and str(pops[i]).strip() != '' else None,
                        'reliability': reliabilities[i] if i < len(reliabilities) and reliabilities[i] else None
                    }
            
            temp_data_map = {}
            for i, date_str in enumerate(temp_dates):
                temp_data_map[date_str] = {
                    'temp_max': temps_max[i] if i < len(temps_max) and temps_max[i] and str(temps_max[i]).strip() != '' else None,
                    'temp_min': temps_min[i] if i < len(temps_min) and temps_min[i] and str(temps_min[i]).strip() != '' else None,
                    'temp_max_upper': temps_max_upper[i] if i < len(temps_max_upper) and temps_max_upper[i] and str(temps_max_upper[i]).strip() != '' else None,
                    'temp_max_lower': temps_max_lower[i] if i < len(temps_max_lower) and temps_max_lower[i] and str(temps_max_lower[i]).strip() != '' else None,
                    'temp_min_upper': temps_min_upper[i] if i < len(temps_min_upper) and temps_min_upper[i] and str(temps_min_upper[i]).strip() != '' else None,
                    'temp_min_lower': temps_min_lower[i] if i < len(temps_min_lower) and temps_min_lower[i] and str(temps_min_lower[i]).strip() != '' else None
                }
            
            # Collect all dates (from both weather and temperature)
            all_dates = set(weather_dates + temp_dates)
            
            # Organize weekly forecast data
            weekly_forecast = []
            for date_str in sorted(all_dates)[:7]:  # Maximum 7 days, sorted by date
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d')
                    weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date_obj.weekday()]
                except:
                    formatted_date = f"Day{len(weekly_forecast)+1}"
                    weekday = ""
                
                # Get weather data
                weather_data = weather_data_map.get(date_str, {})
                weather_code = weather_data.get('weather_code')
                pop_value = weather_data.get('pop')
                reliability = weather_data.get('reliability')
                
                # Get temperature data
                temp_data = temp_data_map.get(date_str, {})
                temp_max_value = temp_data.get('temp_max')
                temp_min_value = temp_data.get('temp_min')
                
                day_data = {
                    'date': formatted_date,
                    'weekday': weekday,
                    'weather_code': weather_code,
                    'weather_desc': self._get_weather_description_from_code(weather_code) if weather_code else None,
                    'pop': pop_value,
                    'reliability': reliability,
                    'temp_max': temp_max_value,
                    'temp_min': temp_min_value,
                    'temp_max_upper': temp_data.get('temp_max_upper'),
                    'temp_max_lower': temp_data.get('temp_max_lower'),
                    'temp_min_upper': temp_data.get('temp_min_upper'),
                    'temp_min_lower': temp_data.get('temp_min_lower')
                }
                weekly_forecast.append(day_data)
                
                logger.debug(f"{formatted_date}({weekday}): weather={weather_code}, pop={pop_value}%, temp={temp_max_value}/{temp_min_value}°C")
            
            logger.info(f"Weekly forecast data acquired: {len(weekly_forecast)} days")
            return weekly_forecast
            
        except Exception as e:
            logger.error(f"Failed to parse weekly forecast data: {e}")
            return None
    
    def _get_weather_description_from_code(self, code):
        """Get weather description from weather code"""
        weather_map = {
            '100': 'Sunny', '101': 'Partly Cloudy', '102': 'Sunny/Rain', '103': 'Partly Rainy',
            '104': 'Sunny/Snow', '105': 'Sunny/Snow', '106': 'Sunny/Rain or Snow', '107': 'Partly Rain/Snow',
            '108': 'Sunny/Thunderstorm', '110': 'Sunny then Cloudy', '111': 'Sunny then Cloudy',
            '112': 'Sunny then Rain', '113': 'Sunny then Rain', '114': 'Sunny then Rain',
            '115': 'Sunny then Snow', '116': 'Sunny then Snow', '117': 'Sunny then Snow',
            '118': 'Sunny then Rain/Snow', '119': 'Sunny then Storm', '120': 'Sunny/Morning Rain',
            '121': 'Sunny/Morning Rain', '122': 'Sunny/Evening Rain', '123': 'Sunny/Mountain Storm',
            '124': 'Sunny/Mountain Snow', '125': 'Sunny/PM Storm', '126': 'Sunny/Midday Rain',
            '127': 'Sunny/Evening Rain', '128': 'Sunny/Night Rain', '130': 'Morning Fog then Sunny',
            '131': 'Sunny/Dawn Fog', '132': 'Sunny/Morning Evening Cloudy', '140': 'Sunny/Rain & Storm',
            '200': 'Cloudy', '201': 'Partly Sunny', '202': 'Cloudy/Rain', '203': 'Partly Rainy',
            '204': 'Cloudy/Snow', '205': 'Cloudy/Snow', '206': 'Cloudy/Rain or Snow', '207': 'Cloudy/Rain or Snow',
            '208': 'Cloudy/Thunderstorm', '209': 'Fog', '210': 'Cloudy then Sunny', '211': 'Cloudy then Sunny',
            '212': 'Cloudy then Rain', '213': 'Cloudy then Rain', '214': 'Cloudy then Rain',
            '215': 'Cloudy then Snow', '216': 'Cloudy then Snow', '217': 'Cloudy then Snow',
            '218': 'Cloudy then Rain/Snow', '219': 'Cloudy then Storm', '220': 'Cloudy/Morning Evening Rain',
            '221': 'Cloudy/Morning Rain', '222': 'Cloudy/Evening Rain', '223': 'Cloudy/Midday Sunny',
            '224': 'Cloudy/Midday Rain', '225': 'Cloudy/Evening Rain', '226': 'Cloudy/Night Rain',
            '228': 'Cloudy/Midday Snow', '229': 'Cloudy/Evening Snow', '230': 'Cloudy/Night Snow',
            '231': 'Cloudy/Sea Fog', '240': 'Cloudy/Rain & Storm', '250': 'Cloudy/Snow & Storm',
            '260': 'Cloudy/Snow or Rain', '270': 'Cloudy/Snow or Rain', '281': 'Cloudy/Midday Snow/Rain',
            '300': 'Rain', '301': 'Rain/Sunny', '302': 'Rain/Stop', '303': 'Rain/Snow',
            '304': 'Rain or Snow', '306': 'Heavy Rain', '308': 'Rain/Strong Wind', '309': 'Rain/Snow',
            '311': 'Rain then Sunny', '313': 'Rain then Cloudy', '314': 'Rain then Snow', '315': 'Rain then Snow',
            '316': 'Rain/Snow then Sunny', '317': 'Rain/Snow then Cloudy', '320': 'Morning Rain then Sunny',
            '321': 'Morning Rain then Cloudy', '322': 'Rain/Morning Evening Snow', '323': 'Rain/Midday Sunny',
            '324': 'Rain/Evening Sunny', '325': 'Rain/Night Sunny', '326': 'Rain/Evening Snow',
            '327': 'Rain/Night Snow', '328': 'Heavy Rain', '329': 'Rain/Sleet',
            '340': 'Snow or Rain', '350': 'Rain/Thunder', '361': 'Snow/Rain then Sunny',
            '371': 'Snow/Rain then Cloudy', '400': 'Snow', '401': 'Snow/Sunny', '402': 'Snow/Stop',
            '403': 'Snow/Rain', '405': 'Heavy Snow', '406': 'Strong Snow/Wind', '407': 'Blizzard',
            '409': 'Snow/Rain', '411': 'Snow then Sunny', '413': 'Snow then Cloudy', '414': 'Snow then Rain',
            '420': 'Morning Snow then Sunny', '421': 'Morning Snow then Cloudy', '422': 'Snow/Midday Sunny',
            '423': 'Snow/Evening Sunny', '424': 'Snow/Night Sunny', '425': 'Heavy Snow',
            '426': 'Snow then Sleet', '427': 'Snow/Sleet', '450': 'Snow/Thunder'
        }
        return weather_map.get(code, 'Unknown')
    
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
    
    def get_weather_emoji(self, weather_code):
        """Get weather emoji icon from weather code"""
        emoji_map = {
            # Sunny series
            '100': '☀️', '101': '🌤️', '102': '🌦️', '103': '🌦️',
            '104': '🌨️', '105': '🌨️', '106': '🌨️', '107': '🌨️',
            '108': '⛈️', '110': '🌤️', '111': '☁️',
            '112': '🌦️', '113': '🌦️', '114': '🌧️',
            '115': '🌨️', '116': '🌨️', '117': '❄️',
            '118': '🌨️', '119': '⛈️', '120': '🌦️',
            '121': '🌦️', '122': '🌦️', '123': '⛈️',
            '124': '🌨️', '125': '⛈️', '126': '🌧️',
            '127': '🌧️', '128': '🌧️', '130': '🌫️',
            '131': '🌫️', '132': '🌤️', '140': '⛈️',
            
            # Cloudy series
            '200': '☁️', '201': '⛅', '202': '🌦️', '203': '🌦️',
            '204': '🌨️', '205': '🌨️', '206': '🌨️', '207': '🌨️',
            '208': '⛈️', '209': '🌫️', '210': '⛅', '211': '⛅',
            '212': '🌦️', '213': '🌦️', '214': '🌧️',
            '215': '🌨️', '216': '🌨️', '217': '❄️',
            '218': '🌨️', '219': '⛈️', '220': '🌦️',
            '221': '🌦️', '222': '🌦️', '223': '⛅',
            '224': '🌧️', '225': '🌧️', '226': '🌧️',
            '228': '❄️', '229': '❄️', '230': '❄️',
            '231': '🌫️', '240': '⛈️', '250': '⛈️',
            '260': '🌨️', '270': '🌨️', '281': '🌨️',
            
            # Rain series
            '300': '🌧️', '301': '🌦️', '302': '🌧️', '303': '🌨️',
            '304': '🌨️', '306': '🌧️', '308': '🌪️', '309': '🌨️',
            '311': '🌦️', '313': '🌧️', '314': '🌨️', '315': '❄️',
            '316': '🌨️', '317': '🌨️', '320': '🌦️',
            '321': '🌧️', '322': '🌨️', '323': '🌦️',
            '324': '🌦️', '325': '🌧️', '326': '🌨️',
            '327': '❄️', '328': '🌧️', '329': '🌨️',
            '340': '🌨️', '350': '⛈️', '361': '🌨️',
            '371': '🌨️',
            
            # Snow series
            '400': '❄️', '401': '🌨️', '402': '❄️', '403': '🌨️',
            '405': '❄️', '406': '🌪️', '407': '🌪️',
            '409': '🌨️', '411': '🌨️', '413': '❄️', '414': '🌨️',
            '420': '🌨️', '421': '❄️', '422': '🌨️',
            '423': '🌨️', '424': '❄️', '425': '❄️',
            '426': '🌨️', '427': '🌨️', '450': '⛈️'
        }
        return emoji_map.get(weather_code, '🌈')
    
    def get_weather_icon_path(self, weather_code):
        """Get local image file path from weather code"""
        # Classify into basic weather patterns
        if weather_code.startswith('1'):  # Sunny series
            if weather_code in ['102', '103', '112', '113', '114', '119', '120', '121', '122', '125', '126', '127', '128', '140']:
                return 'assets/weather_icons/rainy.png'  # Sunny then rain
            elif weather_code in ['104', '105', '115', '116', '117', '124']:
                return 'assets/weather_icons/snowy.png'  # Sunny then snow
            elif weather_code in ['101', '110', '111', '132']:
                return 'assets/weather_icons/partly_cloudy.png'  # Partly cloudy
            else:
                return 'assets/weather_icons/sunny.png'  # Sunny
        
        elif weather_code.startswith('2'):  # Cloudy series
            if weather_code in ['202', '203', '212', '213', '214', '219', '220', '221', '222', '224', '225', '226', '240']:
                return 'assets/weather_icons/rainy.png'  # Cloudy then rain
            elif weather_code in ['204', '205', '215', '216', '217', '228', '229', '230', '250', '260', '270', '281']:
                return 'assets/weather_icons/snowy.png'  # Cloudy then snow
            elif weather_code in ['201', '210', '211', '223']:
                return 'assets/weather_icons/partly_cloudy.png'  # Partly sunny
            else:
                return 'assets/weather_icons/cloudy.png'  # Cloudy
        
        elif weather_code.startswith('3'):  # Rain series
            if weather_code in ['303', '309', '314', '315', '322', '326', '327', '329', '340', '361', '371']:
                return 'assets/weather_icons/snowy.png'  # Rain/snow
            elif weather_code in ['306', '308', '328', '350']:
                return 'assets/weather_icons/storm.png'  # Heavy rain/storm
            else:
                return 'assets/weather_icons/rainy.png'  # Rain
        
        elif weather_code.startswith('4'):  # Snow series
            if weather_code in ['405', '406', '407', '425', '450']:
                return 'assets/weather_icons/storm.png'  # Heavy snow/blizzard
            else:
                return 'assets/weather_icons/snowy.png'  # Snow
        
        else:
            return 'assets/weather_icons/unknown.png'  # Other
    
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
        
        result = {
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
        
        # Add weekly forecast data if available
        if 'weekly_forecast' in weather_data:
            result['weekly_forecast'] = weather_data['weekly_forecast']
        
        return result
    
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
            
            # Process including weekly forecast data
            weekly_data = self._parse_weekly_forecast(forecast_data)
            weather_data = self._parse_weather_data(forecast_data)
            
            if weather_data and weekly_data:
                # Supplement weekly forecast with daily forecast data
                weekly_data = self._supplement_weekly_with_daily_forecast(forecast_data, weekly_data)
                weather_data['weekly_forecast'] = weekly_data
                
            return weather_data
            
        except Exception as e:
            logger.error(f"Error reading data from JSON file: {e}")
            return None