import requests
import csv
import io
import os
import sys
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        # Both Japanese and English keys supported
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
            'Okinawa': 'okinawa',
            # Japanese names
            '北海道': 'hokkaido',
            '青森県': 'aomori',
            '岩手県': 'iwate',
            '宮城県': 'miyagi',
            '秋田県': 'akita',
            '山形県': 'yamagata',
            '福島県': 'fukushima',
            '茨城県': 'ibaraki',
            '栃木県': 'tochigi',
            '群馬県': 'gunma',
            '埼玉県': 'saitama',
            '千葉県': 'chiba',
            '東京都': 'tokyo',
            '神奈川県': 'kanagawa',
            '新潟県': 'niigata',
            '富山県': 'toyama',
            '石川県': 'ishikawa',
            '福井県': 'fukui',
            '山梨県': 'yamanashi',
            '長野県': 'nagano',
            '岐阜県': 'gifu',
            '静岡県': 'shizuoka',
            '愛知県': 'aichi',
            '三重県': 'mie',
            '滋賀県': 'shiga',
            '京都府': 'kyoto',
            '大阪府': 'osaka',
            '兵庫県': 'hyogo',
            '奈良県': 'nara',
            '和歌山県': 'wakayama',
            '鳥取県': 'tottori',
            '島根県': 'shimane',
            '岡山県': 'okayama',
            '広島県': 'hiroshima',
            '山口県': 'yamaguchi',
            '徳島県': 'tokushima',
            '香川県': 'kagawa',
            '愛媛県': 'ehime',
            '高知県': 'kochi',
            '福岡県': 'fukuoka',
            '佐賀県': 'saga',
            '長崎県': 'nagasaki',
            '熊本県': 'kumamoto',
            '大分県': 'oita',
            '宮崎県': 'miyazaki',
            '鹿児島県': 'kagoshima',
            '沖縄県': 'okinawa'
        }
    
    def get_wbgt_forecast_data(self, location=None):
        """
        Get WBGT forecast data
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: WBGT forecast data
        """
        # Check for forced CSV mode
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("Forced CSV mode enabled: Attempting to read data from CSV file...")
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config_en import LOCATIONS
                location = LOCATIONS[0]
            return self._get_wbgt_forecast_from_csv(location)
        
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
                return self._get_wbgt_forecast_from_csv(location)
                
        except Exception as e:
            logger.error(f"Environment Ministry WBGT data retrieval error: {e}")
            logger.info("Attempting to read WBGT forecast data from CSV file...")
            return self._get_wbgt_forecast_from_csv(location)
    
    def get_wbgt_current_data(self, location=None):
        """
        Get WBGT current data
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: WBGT current data
        """
        # Check for forced CSV mode
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("Forced CSV mode enabled: Attempting to read data from CSV file...")
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config_en import LOCATIONS
                location = LOCATIONS[0]
            return self._get_wbgt_current_from_csv(location)
        
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
                return self._get_wbgt_current_from_csv(location)
                
        except Exception as e:
            logger.error(f"Environment Ministry WBGT current data retrieval error: {e}")
            logger.info("Attempting to read WBGT current data from CSV file...")
            return self._get_wbgt_current_from_csv(location)
    
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
                csv_content = response.content.decode('utf-8')
                return self._parse_alert_data(csv_content, prefecture)
            else:
                logger.warning(f"Failed to get Environment Ministry alert data: {response.status_code} - URL: {url}")
                return self._get_alert_from_csv(target_date, file_time, prefecture)
                
        except Exception as e:
            logger.error(f"Environment Ministry alert data retrieval error: {e}")
            logger.info("Attempting to read alert data from CSV file...")
            return self._get_alert_from_csv(target_date, file_time, prefecture)
    
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

    def get_wbgt_forecast_timeseries(self, location=None):
        """
        Get WBGT forecast time series data
        
        Args:
            location (dict): Location information (including prefecture)
            
        Returns:
            dict: Time series WBGT forecast data
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
            logger.info(f"WBGT forecast time series data URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_forecast_timeseries_csv_data(response.text, location)
            else:
                logger.warning(f"Failed to get Environment Ministry WBGT time series data: {response.status_code} - URL: {url}")
                return self._get_wbgt_timeseries_from_csv(location)
                
        except Exception as e:
            logger.error(f"Environment Ministry WBGT time series data retrieval error: {e}")
            logger.info("Attempting to read WBGT time series data from CSV file...")
            return self._get_wbgt_timeseries_from_csv(location)

    def _parse_forecast_timeseries_csv_data(self, csv_content, location):
        """Parse forecast time series CSV data"""
        try:
            from datetime import datetime, timedelta
            
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # 1st line: time headers
            time_headers = lines[0].split(',')[2:]  # Skip first 2 columns
            
            # From 2nd line onwards: location data
            data_lines = lines[1:]
            target_location_code = location.get('wbgt_location_code')
            
            # Search for data for specified location
            for data_row_str in data_lines:
                data_row = data_row_str.split(',')
                if len(data_row) >= 3 and data_row[0] == target_location_code:
                    location_code = data_row[0]
                    update_time = data_row[1]
                    
                    # Create time series data
                    timeseries_data = []
                    for i, time_str in enumerate(time_headers):
                        if i + 2 < len(data_row) and data_row[i + 2].strip():
                            try:
                                # WBGT value is multiplied by 10, so divide by 10
                                wbgt_val = int(data_row[i + 2].strip()) / 10.0
                                
                                # Parse time string (YYYYMMDDHH format)
                                if len(time_str.strip()) == 10:
                                    year = int(time_str[0:4])
                                    month = int(time_str[4:6])
                                    day = int(time_str[6:8])
                                    hour = int(time_str[8:10])
                                    
                                    # Convert 24:00 to 00:00 of next day
                                    if hour == 24:
                                        dt = datetime(year, month, day) + timedelta(days=1)
                                    else:
                                        dt = datetime(year, month, day, hour)
                                    
                                    timeseries_data.append({
                                        'datetime': dt,
                                        'wbgt_value': wbgt_val,
                                        'datetime_str': dt.strftime('%m/%d %H:%M')
                                    })
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Time series data parsing error (time: {time_str}): {e}")
                                continue
                    
                    if timeseries_data:
                        return {
                            'location_code': location_code,
                            'location_name': location.get('name'),
                            'update_time': update_time,
                            'timeseries': timeseries_data,
                            'data_type': 'forecast_timeseries',
                            'source': 'Environment Ministry Heat Stroke Prevention Information Site (Forecast Time Series)'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Forecast time series CSV data parsing error: {e}")
            return None
    
    def _parse_current_csv_data(self, csv_content, location):
        """Parse current CSV data"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            target_location_code = location.get('wbgt_location_code')
            
            # Get location code index from header row
            header = lines[0].split(',')
            target_column_index = -1
            
            for i, column_name in enumerate(header):
                if column_name.strip() == target_location_code:
                    target_column_index = i
                    break
            
            if target_column_index == -1:
                logger.warning(f"Location code {target_location_code} not found in header: {header}")
                return None
            
            # Search from latest data rows (bottom to top)
            for line in reversed(lines[1:]):  # Skip header row
                data = line.split(',')
                if len(data) > target_column_index:
                    date_time = f"{data[0]} {data[1]}" if len(data) > 1 else data[0]
                    
                    try:
                        # Current values don't need division by 10 (already actual values)
                        wbgt_val = float(data[target_column_index]) if data[target_column_index].strip() else None
                        
                        if wbgt_val is not None:
                            return {
                                'wbgt_value': wbgt_val,
                                'location_code': target_location_code,
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
                # Include prefecture data lines (comma-separated with 8+ items)
                if (not line.startswith('Title,') and 
                    not line.startswith('Encoding,') and 
                    not line.startswith('TimeZone,') and 
                    not line.startswith('CreateDate,') and 
                    not line.startswith('CreateTime,') and 
                    not line.startswith('PublishingOffice,') and 
                    not line.startswith('ReportDate,') and 
                    not line.startswith('ReportTime,') and 
                    not line.startswith('TargetDate') and 
                    not line.startswith('TargetTime') and 
                    not line.startswith('DurationTime') and 
                    not line.startswith('BriefComment') and 
                    not line.startswith('KeyMessage') and 
                    not line.startswith('FlagExplanation') and 
                    not line.startswith('Status') and 
                    not line.startswith('InternalFlag') and
                    not line.startswith('府県予報区,') and
                    line.strip() and
                    len(line.split(',')) >= 8):  # Prefecture data lines have minimum 8 items
                    data_lines.append(line)
                    logger.debug(f"Added data line: {line[:50]}...")
            
            logger.info(f"Extracted {len(data_lines)} lines of data from alert CSV")
            
            # Parse CSV data lines
            for line in data_lines:
                data = line.split(',')
                if len(data) >= 8:  # Prefecture data lines have minimum 8 items
                    prefecture_name = data[4] if len(data) > 4 else ''
                    target_date1_flag = data[6] if len(data) > 6 else '0'
                    target_date2_flag = data[7] if len(data) > 7 else '0'
                    
                    logger.debug(f"Prefecture: {prefecture_name}, Flag1: {target_date1_flag}, Flag2: {target_date2_flag}")
                    logger.debug(f"target_prefecture='{target_prefecture}', prefecture_name='{prefecture_name}'")
                    logger.debug(f"target_short='{target_prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', '')}'")
                    
                    # Search for target prefecture data (partial match of prefecture name)
                    target_short = target_prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', '')
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
        logger.debug(f"Alert flag analysis: flag_value='{flag_value}' (type: {type(flag_value)})")
        
        flag_map = {
            '0': {'status': 'No Alert', 'level': 0, 'message': ''},
            '1': {'status': 'Heat Stroke Alert', 'level': 3, 'message': 'Please be alert for heat stroke'},
            '2': {'status': 'Heat Stroke Special Alert (Assessment)', 'level': 2, 'message': 'May reach heat stroke special alert criteria'},
            '3': {'status': 'Heat Stroke Special Alert', 'level': 4, 'message': 'Heat stroke special alert issued. Dangerous heat conditions.'},
            '9': {'status': 'Outside Alert Hours', 'level': 0, 'message': 'Outside alert hours'}
        }
        
        result = flag_map.get(str(flag_value), {'status': 'No Information', 'level': 0, 'message': ''})
        logger.debug(f"Alert flag analysis result: {result}")
        return result
    
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
    
    def _get_wbgt_forecast_from_csv(self, location):
        """Get WBGT forecast data from CSV file (fallback when API access fails)"""
        try:
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # Build CSV file path
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'wbgt_forecast_{pref_name}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"WBGT forecast CSV file not found: {csv_file}")
                return None
            
            # Check file modification time (whether within 24 hours)
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24 hours
                logger.warning(f"WBGT forecast CSV file is too old ({(current_time - file_mtime) / 3600:.1f} hours ago)")
                return None
            
            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"Successfully read WBGT forecast data from CSV file: {csv_file}")
            return self._parse_forecast_csv_data(csv_content, location)
            
        except Exception as e:
            logger.error(f"Error reading WBGT forecast data from CSV file: {e}")
            return None
    
    def _get_wbgt_current_from_csv(self, location):
        """Get WBGT current data from CSV file (fallback when API access fails)"""
        try:
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            now = datetime.now()
            year_month = f"{now.year}{now.month:02d}"
            
            # Build CSV file path
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'wbgt_current_{pref_name}_{year_month}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"WBGT current CSV file not found: {csv_file}")
                return None
            
            # Check file modification time (whether within 6 hours)
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 6 * 3600:  # 6 hours
                logger.warning(f"WBGT current CSV file is too old ({(current_time - file_mtime) / 3600:.1f} hours ago)")
                return None
            
            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"Successfully read WBGT current data from CSV file: {csv_file}")
            return self._parse_current_csv_data(csv_content, location)
            
        except Exception as e:
            logger.error(f"Error reading WBGT current data from CSV file: {e}")
            return None
    
    def _get_wbgt_timeseries_from_csv(self, location):
        """Get WBGT time series data from CSV file (fallback when API access fails)"""
        try:
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # Build CSV file path
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'wbgt_forecast_{pref_name}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"WBGT time series CSV file not found: {csv_file}")
                return None
            
            # Check file modification time (whether within 24 hours)
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24 hours
                logger.warning(f"WBGT time series CSV file is too old ({(current_time - file_mtime) / 3600:.1f} hours ago)")
                return None
            
            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"Successfully read WBGT time series data from CSV file: {csv_file}")
            return self._parse_forecast_timeseries_csv_data(csv_content, location)
            
        except Exception as e:
            logger.error(f"Error reading WBGT time series data from CSV file: {e}")
            return None
    
    def _get_alert_from_csv(self, target_date, file_time, prefecture):
        """Get alert data from CSV file (fallback when API access fails)"""
        try:
            # Build CSV file path
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'alert_{target_date}_{file_time}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"Alert CSV file not found: {csv_file}")
                return None
            
            # Check file modification time (whether within 24 hours)
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24 hours
                logger.warning(f"Alert CSV file is too old ({(current_time - file_mtime) / 3600:.1f} hours ago)")
                return None
            
            # Read CSV file
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"Successfully read alert data from CSV file: {csv_file}")
            return self._parse_alert_data(csv_content, prefecture)
            
        except Exception as e:
            logger.error(f"Error reading alert data from CSV file: {e}")
            return None