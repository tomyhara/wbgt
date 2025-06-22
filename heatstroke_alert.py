import requests
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HeatstrokeAlert:
    def __init__(self):
        self.base_url = "https://www.jma.go.jp/bosai/forecast/data/forecast"
        self.area_codes = {
            '北海道': '016000',
            '青森県': '020000',
            '岩手県': '030000',
            '宮城県': '040000',
            '秋田県': '050000',
            '山形県': '060000',
            '福島県': '070000',
            '茨城県': '080000',
            '栃木県': '090000',
            '群馬県': '100000',
            '埼玉県': '110000',
            '千葉県': '120000',
            '東京都': '130000',
            '神奈川県': '140000',
            '新潟県': '150000',
            '富山県': '160000',
            '石川県': '170000',
            '福井県': '180000',
            '山梨県': '190000',
            '長野県': '200000',
            '岐阜県': '210000',
            '静岡県': '220000',
            '愛知県': '230000',
            '三重県': '240000',
            '滋賀県': '250000',
            '京都府': '260000',
            '大阪府': '270000',
            '兵庫県': '280000',
            '奈良県': '290000',
            '和歌山県': '300000',
            '鳥取県': '310000',
            '島根県': '320000',
            '岡山県': '330000',
            '広島県': '340000',
            '山口県': '350000',
            '德島県': '360000',
            '香川県': '370000',
            '愛媛県': '380000',
            '高知県': '390000',
            '福岡県': '400000',
            '佐賀県': '410000',
            '長崎県': '420000',
            '熊本県': '430000',
            '大分県': '440000',
            '宮崎県': '450000',
            '鹿児島県': '460100',
            '沖縄県': '471000'
        }
    
    def get_alert_data(self, prefecture='東京都'):
        area_code = self.area_codes.get(prefecture, '130000')
        url = f"{self.base_url}/{area_code}.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_alert_data(data, prefecture)
        except requests.exceptions.RequestException as e:
            logger.error(f"熱中症警戒アラート情報の取得に失敗しました: {e}")
            return self._get_fallback_alert()
        except Exception as e:
            logger.error(f"データの解析に失敗しました: {e}")
            return self._get_fallback_alert()
    
    def _parse_alert_data(self, data, prefecture):
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            forecast_data = data[0]
            timeSeries = forecast_data.get('timeSeries', [])
            
            alerts = {
                'today': {'status': '情報なし', 'level': 0, 'message': ''},
                'tomorrow': {'status': '情報なし', 'level': 0, 'message': ''},
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
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        except Exception as e:
            logger.error(f"アラートデータの解析エラー: {e}")
            return self._get_fallback_alert()
    
    def _get_alert_from_weather_code(self, code):
        code = str(code)
        
        if code.startswith('1') or code.startswith('2'):
            return {
                'status': '注意',
                'level': 1,
                'message': '熱中症に注意してください'
            }
        elif code.startswith('3'):
            return {
                'status': '警戒',
                'level': 2,
                'message': '熱中症に警戒してください'
            }
        else:
            return {
                'status': '情報なし',
                'level': 0,
                'message': ''
            }
    
    def _get_fallback_alert(self):
        return {
            'prefecture': '不明',
            'alerts': {
                'today': {'status': 'エラー', 'level': 0, 'message': 'データを取得できませんでした'},
                'tomorrow': {'status': 'エラー', 'level': 0, 'message': 'データを取得できませんでした'},
            },
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_alert_color(self, level):
        colors = {
            0: 'gray',
            1: 'orange',
            2: 'red',
            3: 'darkred'
        }
        return colors.get(level, 'gray')