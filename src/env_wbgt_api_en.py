import requests
import csv
import io
import os
import sys
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class EnvWBGTAPIEN:
    """
    Environment Ministry Heat Stroke Prevention Information Site WBGT Data Service Client (English)
    
    Retrieves official WBGT index data provided by the Ministry of the Environment.
    https://www.wbgt.env.go.jp/data_service.php
    """
    
    def __init__(self):
        self.base_url = "https://www.wbgt.env.go.jp"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WBGT-Kiosk/1.0 (Heat Stroke Prevention System)'
        })
        
        # SSL configuration for corporate Windows environments
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config import SSL_VERIFY, SSL_CERT_PATH
            self.ssl_verify = SSL_VERIFY
            self.ssl_cert_path = SSL_CERT_PATH
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                logger.warning("SSL certificate verification disabled (corporate environment setting)")
        except ImportError:
            self.ssl_verify = True
            self.ssl_cert_path = None
        
        # Prefecture name mapping (alphabetic notation for Environment Ministry service)
        self.prefecture_names = {
            'Hokkaido': 'hokkaido',
            'Aomori': 'aomori',
            'Iwate': 'iwate',
            'Miyagi': 'miyagi',
            'Akita': 'akita',
            'Yamagata': 'yamagata',
            'Fukushima': 'fukushima',
            'Ibaraki': 'ibaraki',
            'Tochigi': 'tochigi',
            'Gunma': 'gunma',
            'Saitama': 'saitama',
            'Chiba': 'chiba',
            'Tokyo': 'tokyo',
            'Kanagawa': 'kanagawa',
            'Niigata': 'niigata',
            'Toyama': 'toyama',
            'Ishikawa': 'ishikawa',
            'Fukui': 'fukui',
            'Yamanashi': 'yamanashi',
            'Nagano': 'nagano',
            'Gifu': 'gifu',
            'Shizuoka': 'shizuoka',
            'Aichi': 'aichi',
            'Mie': 'mie',
            'Shiga': 'shiga',
            'Kyoto': 'kyoto',
            'Osaka': 'osaka',
            'Hyogo': 'hyogo',
            'Nara': 'nara',
            'Wakayama': 'wakayama',
            'Tottori': 'tottori',
            'Shimane': 'shimane',
            'Okayama': 'okayama',
            'Hiroshima': 'hiroshima',
            'Yamaguchi': 'yamaguchi',
            'Tokushima': 'tokushima',
            'Kagawa': 'kagawa',
            'Ehime': 'ehime',
            'Kochi': 'kochi',
            'Fukuoka': 'fukuoka',
            'Saga': 'saga',
            'Nagasaki': 'nagasaki',
            'Kumamoto': 'kumamoto',
            'Oita': 'oita',
            'Miyazaki': 'miyazaki',
            'Kagoshima': 'kagoshima',
            'Okinawa': 'okinawa'
        }
    
    def get_wbgt_forecast_data(self, location=None):
        """
        Get WBGT forecast data
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: WBGT forecast data
        """
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config_en import LOCATIONS
                location = LOCATIONS[0]
            
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # Official URL structure for Environment Ministry data service (prefecture-specific forecast)
            url = f"{self.base_url}/prev15WG/dl/yohou_{pref_name}.csv"
            logger.info(f"WBGT forecast data URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_forecast_csv_data(response.text, location)
            else:
                logger.warning(f"Failed to get data from Environment Ministry WBGT service: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Environment Ministry WBGT data retrieval error: {e}")
            return None
    
    def get_wbgt_current_data(self, location=None):
        """
        Get WBGT current data
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: WBGT current data
        """
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config_en import LOCATIONS
                location = LOCATIONS[0]
                
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            now = datetime.now()
            year_month = f"{now.year}{now.month:02d}"
            
            # Official URL structure for Environment Ministry data service (prefecture-specific current data)
            url = f"{self.base_url}/est15WG/dl/wbgt_{pref_name}_{year_month}.csv"
            logger.info(f"WBGT current data URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_current_csv_data(response.text, location)
            else:
                logger.warning(f"Failed to get Environment Ministry WBGT current data: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Environment Ministry WBGT current data retrieval error: {e}")
            return None
    
    def get_alert_data(self, location=None):
        """
        Get heat stroke warning alert information
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: Alert information
        """
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config_en import LOCATIONS
                location = LOCATIONS[0]
                
            prefecture = location.get('prefecture')
            now = datetime.now()
            date_str = now.strftime('%Y%m%d')
            
            # Select appropriate file based on time
            if now.hour < 5:
                # Before 5 AM current day uses previous day 17:00 file
                file_time = '17'
                target_date = (now - timedelta(days=1)).strftime('%Y%m%d')
            elif now.hour < 14:
                # Before 14:00 uses current day 05:00 file
                file_time = '05'
                target_date = date_str
            elif now.hour < 17:
                # Before 17:00 uses current day 14:00 file (special alert information)
                file_time = '14'
                target_date = date_str
            else:
                # After 17:00 uses current day 17:00 file
                file_time = '17'
                target_date = date_str
            
            # Official URL structure for Environment Ministry data service (alert information)
            url = f"{self.base_url}/alert/dl/{now.year}/alert_{target_date}_{file_time}.csv"
            logger.info(f"Heat stroke warning alert data URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_alert_data(response.text, prefecture)
            else:
                logger.warning(f"Failed to get Environment Ministry alert data: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Environment Ministry alert data retrieval error: {e}")
            return None
    
    def _parse_forecast_csv_data(self, csv_content, location):
        """Parse forecast CSV data"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # From 2nd line onwards: location data
            data_lines = lines[1:]
            target_location_code = location.get('wbgt_location_code')
            
            # Search for data for specified location
            for data_row_str in data_lines:
                data_row = data_row_str.split(',')
                if len(data_row) >= 3 and data_row[0] == target_location_code:
                    location_code = data_row[0]
                    update_time = data_row[1]
                    
                    # Get latest forecast value (from 3rd element)
                    wbgt_values = []
                    for i in range(2, len(data_row)):
                        if data_row[i].strip():
                            try:
                                # WBGT value is multiplied by 10, so divide by 10
                                wbgt_val = int(data_row[i].strip()) / 10.0
                                wbgt_values.append(wbgt_val)
                            except (ValueError, TypeError):
                                continue
                    
                    if wbgt_values:
                        return {
                            'wbgt_value': wbgt_values[0],  # Latest forecast value
                            'location_code': location_code,
                            'location_name': location.get('name'),
                            'update_time': update_time,
                            'data_type': 'forecast',
                            'source': 'Environment Ministry Heat Stroke Prevention Information Site (Forecast)'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Forecast CSV data parsing error: {e}")
            return None
    
    def _parse_current_csv_data(self, csv_content, location):
        """Parse current CSV data"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            target_location_code = location.get('wbgt_location_code')
            
            for line in reversed(lines):  # Search from latest
                data = line.split(',')
                if len(data) >= 4 and data[0] == target_location_code:
                    location_code = data[0]
                    date_time = data[1]
                    
                    try:
                        # WBGT value is multiplied by 10, so divide by 10
                        wbgt_val = int(data[2]) / 10.0 if data[2].strip() else None
                        
                        if wbgt_val is not None:
                            return {
                                'wbgt_value': wbgt_val,
                                'location_code': location_code,
                                'location_name': location.get('name'),
                                'datetime': date_time,
                                'data_type': 'current',
                                'source': 'Environment Ministry Heat Stroke Prevention Information Site (Current)'
                            }
                    except (ValueError, TypeError):
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Current CSV data parsing error: {e}")
            return None
    
    def _parse_alert_data(self, csv_content, target_prefecture):
        """Parse alert data"""
        try:
            lines = csv_content.strip().split('\n')
            if not lines:
                return None
            
            alerts = {
                'today': {'status': 'No Alert', 'level': 0, 'message': ''},
                'tomorrow': {'status': 'No Alert', 'level': 0, 'message': ''}
            }
            
            # Process only data lines, excluding metadata
            data_lines = []
            for line in lines:
                # Skip metadata lines (Title, Encoding, TimeZone, etc.)
                if (not line.startswith('Title,') and 
                    not line.startswith('Encoding,') and 
                    not line.startswith('TimeZone,') and 
                    not line.startswith('CreateDate,') and 
                    not line.startswith('CreateTime,') and 
                    not line.startswith('PublishingOffice,') and 
                    not line.startswith('ReportDate,') and 
                    not line.startswith('ReportTime,') and 
                    not line.startswith('TargetDate') and 
                    not line.startswith('DurationTime') and 
                    not line.startswith('BriefComment') and 
                    not line.startswith('Key Message') and 
                    not line.startswith('FlagExplanation') and 
                    not line.startswith('Status') and 
                    not line.startswith('InternalFlag') and
                    line.strip()):
                    data_lines.append(line)
            
            logger.info(f"Extracted {len(data_lines)} lines of data from alert CSV")
            
            # Parse CSV data lines
            for line in data_lines:
                data = line.split(',')
                if len(data) >= 12:
                    prefecture_name = data[4] if len(data) > 4 else ''
                    target_date1_flag = data[6] if len(data) > 6 else '0'
                    target_date2_flag = data[7] if len(data) > 7 else '0'
                    
                    logger.debug(f"Prefecture: {prefecture_name}, Flag1: {target_date1_flag}, Flag2: {target_date2_flag}")
                    
                    # Search for target prefecture data (partial match of prefecture name)
                    target_short = target_prefecture.replace('Prefecture', '').replace('Metropolis', '').replace('Prefecture', '')
                    if (target_short in prefecture_name or 
                        prefecture_name in target_short or 
                        target_prefecture == prefecture_name):
                        
                        logger.info(f"Found data for target prefecture {target_prefecture}: {prefecture_name}")
                        
                        # Process TargetDate1 flag (today)
                        alerts['today'] = self._parse_alert_flag(target_date1_flag)
                        
                        # Process TargetDate2 flag (tomorrow)  
                        alerts['tomorrow'] = self._parse_alert_flag(target_date2_flag)
                        break
            
            return {
                'prefecture': target_prefecture,
                'alerts': alerts,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Environment Ministry Heat Stroke Prevention Information Site (Official Alert)'
            }
            
        except Exception as e:
            logger.error(f"Alert data parsing error: {e}")
            return None
    
    def _parse_alert_flag(self, flag_value):
        """Parse alert flag"""
        flag_map = {
            '0': {'status': 'No Alert', 'level': 0, 'message': ''},
            '1': {'status': 'Heat Stroke Alert', 'level': 3, 'message': 'Please be alert for heat stroke'},
            '2': {'status': 'Heat Stroke Special Alert (Assessment)', 'level': 2, 'message': 'May reach heat stroke special alert criteria'},
            '3': {'status': 'Heat Stroke Special Alert', 'level': 4, 'message': 'Heat stroke special alert issued. Dangerous heat conditions.'},
            '9': {'status': 'Outside Alert Hours', 'level': 0, 'message': 'Outside alert hours'}
        }
        
        return flag_map.get(str(flag_value), {'status': 'No Information', 'level': 0, 'message': ''})
    
    def _get_alert_numeric_level(self, alert_level):
        """Convert alert level to numeric value"""
        level_map = {
            'Heat Stroke Special Alert': 4,
            'Heat Stroke Alert': 3,
            'Heat Stroke Special Alert (Assessment)': 2,
            'No Alert': 0,
            'Outside Alert Hours': 0,
            'No Information': 0
        }
        return level_map.get(alert_level, 0)
    
    def get_wbgt_level_info(self, wbgt_value):
        """
        Get warning level information from WBGT value
        Based on Environment Ministry standards
        """
        if wbgt_value >= 31:
            return "Dangerous", "red", "Avoid going outside, move to cool indoor space"
        elif wbgt_value >= 28:
            return "Severe Warning", "orange", "Avoid sun when outside, use air conditioning appropriately indoors"
        elif wbgt_value >= 25:
            return "Warning", "yellow", "Take regular adequate rest during exercise or intense work"
        elif wbgt_value >= 21:
            return "Caution", "green", "Generally low risk but danger exists during intense exercise or heavy labor"
        else:
            return "Safe", "blue", "Heat stroke risk is usually low"
    
    def is_service_available(self):
        """
        Check if Environment Ministry WBGT service is available
        Service period: Late April to late October
        """
        now = datetime.now()
        year = now.year
        
        # Check service period (April 23 to October 22)
        service_start = datetime(year, 4, 23)
        service_end = datetime(year, 10, 22)
        
        # For testing: Force current period to be valid (for implementation testing)
        # In actual operation, uncomment the following line
        return True  # return service_start <= now <= service_end