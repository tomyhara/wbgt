import requests
import json
import math
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JMAWeatherAPI:
    def __init__(self, area_code='130000'):
        self.area_code = area_code
        self.base_url = "https://www.jma.go.jp/bosai"
        
        # SSL設定の読み込み（Windows企業環境対応）
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config import SSL_VERIFY, SSL_CERT_PATH
            self.ssl_verify = SSL_VERIFY
            self.ssl_cert_path = SSL_CERT_PATH
            if not self.ssl_verify:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except ImportError:
            self.ssl_verify = True
            self.ssl_cert_path = None
        
        self.area_codes = {
            '札幌': '016000',
            '青森': '020000', 
            '盛岡': '030000',
            '仙台': '040000',
            '秋田': '050000',
            '山形': '060000',
            '福島': '070000',
            '水戸': '080000',
            '宇都宮': '090000',
            '前橋': '100000',
            'さいたま': '110000',
            '千葉': '120000',
            '東京': '130000',
            '横浜': '140000',
            '新潟': '150000',
            '富山': '160000',
            '金沢': '170000',
            '福井': '180000',
            '甲府': '190000',
            '長野': '200000',
            '岐阜': '210000',
            '静岡': '220000',
            '名古屋': '230000',
            '津': '240000',
            '大津': '250000',
            '京都': '260000',
            '大阪': '270000',
            '神戸': '280000',
            '奈良': '290000',
            '和歌山': '300000',
            '鳥取': '310000',
            '松江': '320000',
            '岡山': '330000',
            '広島': '340000',
            '山口': '350000',
            '徳島': '360000',
            '高松': '370000',
            '松山': '380000',
            '高知': '390000',
            '福岡': '400000',
            '佐賀': '410000',
            '長崎': '420000',
            '熊本': '430000',
            '大分': '440000',
            '宮崎': '450000',
            '鹿児島': '460100',
            '那覇': '471000'
        }
    
    def get_current_weather(self):
        """現在の天気データを取得"""
        # 強制CSV モードの確認
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("強制CSVモードが有効: CSVファイルからのデータ読み込みを試行中...")
            return self._get_weather_from_csv()
        
        try:
            forecast_url = f"{self.base_url}/forecast/data/forecast/{self.area_code}.json"
            response = requests.get(forecast_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            forecast_data = response.json()
            
            # 観測データも取得
            obs_url = f"{self.base_url}/amedas/const/amedastable.json"
            obs_response = requests.get(obs_url, timeout=10, verify=self.ssl_verify)
            obs_response.raise_for_status()
            
            return self._parse_weather_data(forecast_data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"気象データの取得に失敗しました: {e}")
            logger.info("CSVファイルからのデータ読み込みを試行中...")
            return self._get_weather_from_csv()
        except Exception as e:
            logger.error(f"データ解析エラー: {e}")
            logger.info("CSVファイルからのデータ読み込みを試行中...")
            return self._get_weather_from_csv()
    
    def _parse_weather_data(self, forecast_data):
        """予報データを解析"""
        try:
            # 基本情報取得
            publishing_office = forecast_data[0]['publishingOffice']
            report_datetime = forecast_data[0]['reportDatetime']
            
            # 今日の予報を取得
            time_series = forecast_data[0]['timeSeries']
            
            # 天気予報データ
            weather_data = time_series[0]
            areas = weather_data['areas'][0]
            
            # 今日の天気
            weather_code = areas['weatherCodes'][0] if areas.get('weatherCodes') else '100'
            weather_desc_raw = areas['weathers'][0] if areas.get('weathers') else '晴れ'
            weather_desc = self._simplify_weather_description(weather_desc_raw)
            
            # 気温データを取得
            current_temp = None
            forecast_high = None
            forecast_low = None
            
            # JMA予報データから気温を取得
            for ts in time_series:
                if 'temps' in ts:
                    # 気温予報データが含まれている
                    areas_temp = ts.get('areas', [])
                    if areas_temp:
                        temps = areas_temp[0].get('temps', [])
                        if len(temps) >= 2:
                            # 最低気温と最高気温
                            forecast_low = int(temps[0]) if temps[0] else None
                            forecast_high = int(temps[1]) if temps[1] else None
            
            # 現在気温と予想気温のデフォルト値
            if not current_temp:
                # 天気コードから現在気温を推定
                temp_humidity = self._estimate_temp_humidity_from_weather(weather_code, weather_desc)
                current_temp = temp_humidity['temperature']
                humidity = temp_humidity['humidity']
            else:
                humidity = 60  # デフォルト湿度
            
            # 予想最高気温がない場合は現在気温をベースに推定
            if not forecast_high:
                forecast_high = current_temp + 3
            if not forecast_low:
                forecast_low = current_temp - 2
            
            return {
                'temperature': current_temp,
                'forecast_high': forecast_high,
                'forecast_low': forecast_low,
                'humidity': humidity,
                'weather_description': weather_desc,
                'weather_code': weather_code,
                'pressure': 1013,  # 標準気圧
                'wind_speed': 0,
                'publishing_office': publishing_office,
                'report_datetime': report_datetime
            }
            
        except Exception as e:
            logger.error(f"天気データの解析に失敗: {e}")
            return None
    
    def _estimate_temp_humidity_from_weather(self, weather_code, weather_desc):
        """天気コードから気温と湿度を推定"""
        # 現在の季節を考慮
        month = datetime.now().month
        
        # 季節による基本気温
        if month in [12, 1, 2]:  # 冬
            base_temp = 8
        elif month in [3, 4, 5]:  # 春
            base_temp = 18
        elif month in [6, 7, 8]:  # 夏
            base_temp = 28
        else:  # 秋
            base_temp = 20
        
        # 天気による調整
        if '晴' in weather_desc:
            temp_adj = 2
            humidity = 50
        elif '曇' in weather_desc:
            temp_adj = 0
            humidity = 65
        elif '雨' in weather_desc:
            temp_adj = -3
            humidity = 85
        elif '雪' in weather_desc:
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
        """天気の説明を短縮"""
        if not weather_desc:
            return "不明"
        
        # 全角スペースと半角スペースを除去
        cleaned = weather_desc.replace('　', '').replace(' ', '')
        
        # 長い文章を短縮
        if '晴' in cleaned:
            if '時々' in cleaned or 'のち' in cleaned:
                return "晴れ時々曇り" if '曇' in cleaned else "晴れ"
            return "晴れ"
        elif '曇' in cleaned:
            if '雨' in cleaned or '雷' in cleaned:
                return "曇り時々雨"
            elif '晴' in cleaned:
                return "曇り時々晴れ"
            return "曇り"
        elif '雨' in cleaned:
            if '雷' in cleaned:
                return "雨・雷"
            elif '雪' in cleaned:
                return "雨・雪"
            return "雨"
        elif '雪' in cleaned:
            if '雨' in cleaned:
                return "雪・雨"
            return "雪"
        else:
            # その他の場合は最初の10文字まで
            return cleaned[:10]
    
    def calculate_wbgt(self, temp, humidity):
        """WBGT指数を計算"""
        # 湿球温度の計算
        temp_k = temp + 273.15
        es = 6.112 * math.exp(17.67 * temp / (temp + 243.5))
        e = es * humidity / 100
        td = 243.5 * math.log(e / 6.112) / (17.67 - math.log(e / 6.112))
        
        # 屋外でのWBGT計算（日射なしの場合）
        wbgt = 0.7 * td + 0.2 * temp + 3.0
        
        return round(wbgt, 1)
    
    def get_wbgt_level(self, wbgt):
        """WBGT指数から警戒レベルを判定"""
        if wbgt < 21:
            return "注意", "green", "適度な運動は可能"
        elif wbgt < 25:
            return "警戒", "yellow", "積極的な水分補給が必要"
        elif wbgt < 28:
            return "厳重警戒", "orange", "激しい運動は避ける"
        elif wbgt < 31:
            return "危険", "red", "運動は原則中止"
        else:
            return "極めて危険", "darkred", "外出を避ける"
    
    def get_weather_data(self):
        """天気データとWBGT指数を取得"""
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
            'feels_like': round(temp + 2, 1),  # 体感温度の簡易計算
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
        """CSVファイルから天気データを取得（APIアクセス失敗時のフォールバック）"""
        try:
            # JSONファイルのパスを構築
            script_dir = os.path.dirname(os.path.dirname(__file__))
            json_file = os.path.join(script_dir, 'data', 'csv', f'jma_forecast_{self.area_code}.json')
            
            if not os.path.exists(json_file):
                logger.warning(f"JMA JSONファイルが見つかりません: {json_file}")
                return None
            
            # ファイルの更新時間をチェック（24時間以内かどうか）
            file_mtime = os.path.getmtime(json_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24時間
                logger.warning(f"JMA JSONファイルが古すぎます（{(current_time - file_mtime) / 3600:.1f}時間前）")
                return None
            
            # JSONファイルを読み込み
            with open(json_file, 'r', encoding='utf-8') as f:
                forecast_data = json.load(f)
            
            logger.info(f"JSONファイルからデータを正常に読み込みました: {json_file}")
            return self._parse_weather_data(forecast_data)
            
        except Exception as e:
            logger.error(f"JSONファイルからのデータ読み込みエラー: {e}")
            return None