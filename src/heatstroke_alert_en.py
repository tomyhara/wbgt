import requests
import json
import os
import sys
from datetime import datetime, timedelta
import logging
from env_wbgt_api_en import EnvWBGTAPIEN

logger = logging.getLogger(__name__)

class HeatstrokeAlertEN:
    def __init__(self):
        # Prioritize official Environment Ministry data service
        self.env_wbgt_api = EnvWBGTAPIEN()
        
        # Fallback JMA API data
        self.base_url = "https://www.jma.go.jp/bosai/forecast/data/forecast"
        
        # SSL configuration loading (for Windows corporate environments)
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config import SSL_VERIFY, SSL_CERT_PATH
            self.ssl_verify = SSL_VERIFY
            self.ssl_cert_path = SSL_CERT_PATH
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                logger.warning("SSL certificate verification is disabled (corporate environment setting)")
        except ImportError:
            self.ssl_verify = True
            self.ssl_cert_path = None
        self.area_codes = {
            'Hokkaido': '016000',
            'Aomori': '020000',
            'Iwate': '030000',
            'Miyagi': '040000',
            'Akita': '050000',
            'Yamagata': '060000',
            'Fukushima': '070000',
            'Ibaraki': '080000',
            'Tochigi': '090000',
            'Gunma': '100000',
            'Saitama': '110000',
            'Chiba': '120000',
            'Tokyo': '130000',
            'Kanagawa': '140000',
            'Niigata': '150000',
            'Toyama': '160000',
            'Ishikawa': '170000',
            'Fukui': '180000',
            'Yamanashi': '190000',
            'Nagano': '200000',
            'Gifu': '210000',
            'Shizuoka': '220000',
            'Aichi': '230000',
            'Mie': '240000',
            'Shiga': '250000',
            'Kyoto': '260000',
            'Osaka': '270000',
            'Hyogo': '280000',
            'Nara': '290000',
            'Wakayama': '300000',
            'Tottori': '310000',
            'Shimane': '320000',
            'Okayama': '330000',
            'Hiroshima': '340000',
            'Yamaguchi': '350000',
            'Tokushima': '360000',
            'Kagawa': '370000',
            'Ehime': '380000',
            'Kochi': '390000',
            'Fukuoka': '400000',
            'Saga': '410000',
            'Nagasaki': '420000',
            'Kumamoto': '430000',
            'Oita': '440000',
            'Miyazaki': '450000',
            'Kagoshima': '460100',
            'Okinawa': '471000'
        }
    
    def get_alert_data(self, prefecture='Tokyo'):
        """Get heat stroke warning alert information (prioritizing official Environment Ministry data)"""
        
        # First try official Environment Ministry data
        if self.env_wbgt_api.is_service_available():
            # Environment Ministry API expects location object, so create one
            location = {'prefecture': prefecture}
            official_data = self.env_wbgt_api.get_alert_data(location)
            if official_data:
                logger.info("Retrieved official Environment Ministry alert data")
                return self._translate_official_alert_data(official_data)
        
        # Fallback: Estimate from JMA API
        logger.info("Using JMA API to estimate alert information")
        area_code = self.area_codes.get(prefecture, '130000')
        url = f"{self.base_url}/{area_code}.json"
        
        try:
            response = requests.get(url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            data = response.json()
            return self._parse_alert_data(data, prefecture)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get heat stroke warning alert information: {e}")
            return self._get_fallback_alert()
        except Exception as e:
            logger.error(f"Failed to parse data: {e}")
            return self._get_fallback_alert()
    
    def _translate_official_alert_data(self, official_data):
        """Translate official Environment Ministry alert data to English"""
        try:
            alerts = official_data.get('alerts', {})
            translated_alerts = {}
            
            for day, alert in alerts.items():
                status = alert.get('status', '')
                message = alert.get('message', '')
                level = alert.get('level', 0)
                
                # Translate status
                if '発表なし' in status:
                    translated_status = 'No Alert'
                elif '熱中症特別警戒情報' in status:
                    translated_status = 'Heat Stroke Special Alert'
                elif '熱中症警戒情報' in status:
                    translated_status = 'Heat Stroke Alert'
                elif '発表時間外' in status:
                    translated_status = 'Outside Alert Hours'
                else:
                    translated_status = status
                
                # Translate message
                if '熱中症に警戒してください' in message:
                    translated_message = 'Please be alert for heat stroke'
                elif '危険な暑さです' in message:
                    translated_message = 'Dangerous heat conditions'
                elif '熱中症特別警戒情報の基準に達する可能性があります' in message:
                    translated_message = 'May reach heat stroke special alert criteria'
                else:
                    translated_message = message
                
                translated_alerts[day] = {
                    'status': translated_status,
                    'level': level,
                    'message': translated_message
                }
            
            return {
                'prefecture': official_data.get('prefecture', ''),
                'alerts': translated_alerts,
                'last_updated': official_data.get('last_updated', ''),
                'source': 'Official Environment Ministry Data'
            }
            
        except Exception as e:
            logger.error(f"Error translating official alert data: {e}")
            return self._get_fallback_alert()
    
    def _parse_alert_data(self, data, prefecture):
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            forecast_data = data[0]
            timeSeries = forecast_data.get('timeSeries', [])
            
            alerts = {
                'today': {'status': 'No Information', 'level': 0, 'message': ''},
                'tomorrow': {'status': 'No Information', 'level': 0, 'message': ''},
            }
            
            for series in timeSeries:
                if 'areas' in series and len(series['areas']) > 0:
                    area = series['areas'][0]
                    if 'weatherCodes' in area:
                        weather_codes = area['weatherCodes']
                        times = series.get('timeDefines', [])
                        
                        for i, time_str in enumerate(times):
                            date = datetime.fromisoformat(time_str.replace('Z', '+00:00')).date()
                            
                            if i < len(weather_codes):
                                code = weather_codes[i]
                                alert_info = self._get_alert_from_weather_code(code)
                                
                                if date == today:
                                    alerts['today'] = alert_info
                                elif date == tomorrow:
                                    alerts['tomorrow'] = alert_info
            
            return {
                'prefecture': prefecture,
                'alerts': alerts,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'JMA API (Estimated)'
            }
        
        except Exception as e:
            logger.error(f"Alert data parsing error: {e}")
            return self._get_fallback_alert()
    
    def _get_alert_from_weather_code(self, code):
        code = str(code)
        
        if code.startswith('1') or code.startswith('2'):
            return {
                'status': 'Caution',
                'level': 1,
                'message': 'Please be cautious of heat stroke'
            }
        elif code.startswith('3'):
            return {
                'status': 'Warning',
                'level': 2,
                'message': 'Please be alert for heat stroke'
            }
        else:
            return {
                'status': 'No Information',
                'level': 0,
                'message': ''
            }
    
    def _get_fallback_alert(self):
        return {
            'prefecture': 'Unknown',
            'alerts': {
                'today': {'status': 'Error', 'level': 0, 'message': 'Could not retrieve data'},
                'tomorrow': {'status': 'Error', 'level': 0, 'message': 'Could not retrieve data'},
            },
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'Error'
        }
    
    def get_alert_color(self, level):
        colors = {
            0: 'gray',      # No alert
            1: 'orange',    # Caution
            2: 'yellow',    # Special alert (assessment)
            3: 'red',       # Heat stroke alert
            4: 'darkred'    # Heat stroke special alert
        }
        return colors.get(level, 'gray')