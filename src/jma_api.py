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
            
            # 週間予報データも取得
            weekly_data = self._parse_weekly_forecast(forecast_data)
            weather_data = self._parse_weather_data(forecast_data)
            if weather_data and weekly_data:
                # 今日・明日予報から週間予報の最初の日を補完
                weekly_data = self._supplement_weekly_with_daily_forecast(forecast_data, weekly_data)
                weather_data['weekly_forecast'] = weekly_data
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"気象データの取得に失敗しました: {e}")
            logger.info("CSVファイルからのデータ読み込みを試行中...")
            return self._get_weather_from_csv()
        except Exception as e:
            logger.error(f"データ解析エラー: {e}")
            logger.info("CSVファイルからのデータ読み込みを試行中...")
            return self._get_weather_from_csv()
    
    def _supplement_weekly_with_daily_forecast(self, forecast_data, weekly_data):
        """今日・明日予報から週間予報の最初の日を補完"""
        try:
            if not forecast_data or len(forecast_data) < 1 or not weekly_data:
                return weekly_data
            
            daily_series = forecast_data[0]  # Series 0が今日・明日予報
            if 'timeSeries' not in daily_series:
                return weekly_data
            
            # 今日・明日の降水確率を取得
            for ts in daily_series['timeSeries']:
                if 'areas' in ts and ts['areas']:
                    area = ts['areas'][0]
                    if 'pops' in area:
                        time_defines = ts.get('timeDefines', [])
                        pops = area.get('pops', [])
                        
                        # 明日のデータを検索（時間で判断）
                        from datetime import datetime, timedelta
                        tomorrow = datetime.now() + timedelta(days=1)
                        tomorrow_date_str = tomorrow.strftime('%Y-%m-%d')
                        
                        for i, time_str in enumerate(time_defines):
                            if tomorrow_date_str in time_str and i < len(pops) and pops[i]:
                                # 週間予報の最初の日が明日の場合、降水確率を補完
                                if weekly_data and weekly_data[0]['pop'] is None:
                                    weekly_data[0]['pop'] = pops[i]
                                    logger.info(f"明日の降水確率を補完: {pops[i]}%")
                                break
                        break
            
            return weekly_data
            
        except Exception as e:
            logger.warning(f"週間予報の補完処理でエラー: {e}")
            return weekly_data
    
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
                areas_temp = ts.get('areas', [])
                if areas_temp and 'temps' in areas_temp[0]:
                    # 気温予報データが含まれている
                    time_defines = ts.get('timeDefines', [])
                    
                    # 設定で指定された地域名に一致するエリアを探す
                    target_area = None
                    # エリアコードから目標地域名を推定（優先度順）
                    target_names = {
                        '140000': ['横浜'],  # 神奈川県
                        '120000': ['銚子']  # 千葉県（銚子を優先）
                    }
                    
                    possible_names = target_names.get(self.area_code, [])
                    
                    # 最初に具体的な地域名で探す
                    for possible_name in possible_names:
                        for area in areas_temp:
                            area_name = area['area']['name']
                            if area_name == possible_name:  # 完全一致を優先
                                target_area = area
                                logger.info(f"目標地域を発見(完全一致): {area_name}")
                                break
                        if target_area:
                            break
                    
                    # 完全一致がない場合は部分一致で探す
                    if not target_area:
                        for possible_name in possible_names:
                            for area in areas_temp:
                                area_name = area['area']['name']
                                if possible_name in area_name or area_name in possible_name:
                                    target_area = area
                                    logger.info(f"目標地域を発見(部分一致): {area_name}")
                                    break
                            if target_area:
                                break
                    
                    # 目標地域が見つからない場合は最初のエリアを使用
                    if not target_area:
                        target_area = areas_temp[0]
                        logger.warning(f"目標地域が見つからないため、最初のエリアを使用: {target_area['area']['name']}")
                    
                    temps = target_area.get('temps', [])
                    
                    # temps配列の構造: [今日最高, 今日最高(重複), 明日最低, 明日最高]
                    # メインロジック: シンプルに配列から直接取得
                    if len(temps) >= 1 and temps[0]:
                        forecast_high = int(temps[0])  # 今日の最高気温
                        logger.info(f"今日の最高気温を取得: {forecast_high}°C ({target_area['area']['name']})")
                    
                    if len(temps) >= 3 and temps[2]:
                        forecast_low = int(temps[2])   # 明日の最低気温を今日の最低気温として使用
                        logger.info(f"今日の最低気温を取得: {forecast_low}°C ({target_area['area']['name']})")
                    elif len(temps) >= 2 and temps[1]:
                        forecast_low = int(temps[1])   # フォールバック
                        logger.info(f"今日の最低気温を取得(フォールバック): {forecast_low}°C ({target_area['area']['name']})")
                    
                    # 最初のtempsデータを取得したらループ終了
                    break
            
            # 現在気温と予想気温のデフォルト値
            if not current_temp:
                # アメダス実況データから現在気温を取得を試行
                current_temp = self._get_current_temperature_from_amedas()
                
                if not current_temp:
                    # アメダスデータが取得できない場合は天気コードから推定
                    temp_humidity = self._estimate_temp_humidity_from_weather(weather_code, weather_desc)
                    current_temp = temp_humidity['temperature']
                    humidity = temp_humidity['humidity']
                else:
                    humidity = 60  # デフォルト湿度
            else:
                humidity = 60  # デフォルト湿度
            
            # 予想最高・最低気温が取得できない場合のみ推定
            if not forecast_high:
                forecast_high = current_temp + 3
                logger.warning(f"予報最高気温が取得できないため推定値を使用: {forecast_high}°C")
            if not forecast_low:
                forecast_low = current_temp - 2
                logger.warning(f"予報最低気温が取得できないため推定値を使用: {forecast_low}°C")
            
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
    
    def _parse_weekly_forecast(self, forecast_data):
        """週間予報データを解析（改善版）"""
        try:
            if len(forecast_data) < 2:
                logger.warning("週間予報データが見つかりません")
                return None
            
            weekly_series = forecast_data[1]  # Series 1が週間予報
            
            if 'timeSeries' not in weekly_series or len(weekly_series['timeSeries']) < 2:
                logger.warning("週間予報の時系列データが不完全です")
                return None
            
            # 週間天気データ（timeSeries[0]）
            weather_ts = weekly_series['timeSeries'][0]
            weather_areas = weather_ts.get('areas', [])
            if not weather_areas:
                logger.warning("週間予報の地域データが見つかりません")
                return None
            
            weather_area = weather_areas[0]
            weather_dates = weather_ts.get('timeDefines', [])
            weather_codes = weather_area.get('weatherCodes', [])
            pops = weather_area.get('pops', [])
            reliabilities = weather_area.get('reliabilities', [])
            
            logger.info(f"週間天気データ: {weather_area['area']['name']}, 日数: {len(weather_dates)}")
            
            # 週間気温データ（timeSeries[1]）
            temp_ts = weekly_series['timeSeries'][1]
            temp_areas = temp_ts.get('areas', [])
            if not temp_areas:
                logger.warning("週間予報の気温データが見つかりません")
                return None
            
            temp_area = temp_areas[0]
            temp_dates = temp_ts.get('timeDefines', [])
            temps_max = temp_area.get('tempsMax', [])
            temps_min = temp_area.get('tempsMin', [])
            temps_max_upper = temp_area.get('tempsMaxUpper', [])
            temps_max_lower = temp_area.get('tempsMaxLower', [])
            temps_min_upper = temp_area.get('tempsMinUpper', [])
            temps_min_lower = temp_area.get('tempsMinLower', [])
            
            logger.info(f"週間気温データ: {temp_area['area']['name']}, 日数: {len(temp_dates)}")
            
            # データ統合のために日付をベースにマッピング
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
            
            # 全日付を収集（天気と気温の両方から）
            all_dates = set(weather_dates + temp_dates)
            
            # 週間予報データを整理
            weekly_forecast = []
            for date_str in sorted(all_dates)[:7]:  # 最大7日間、日付順
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d')
                    weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
                except:
                    formatted_date = f"Day{len(weekly_forecast)+1}"
                    weekday = ""
                
                # 天気データを取得
                weather_data = weather_data_map.get(date_str, {})
                weather_code = weather_data.get('weather_code')
                pop_value = weather_data.get('pop')
                reliability = weather_data.get('reliability')
                
                # 気温データを取得
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
                
                logger.debug(f"{formatted_date}({weekday}): 天気={weather_code}, 降水確率={pop_value}%, 気温={temp_max_value}/{temp_min_value}°C")
            
            logger.info(f"週間予報データを取得: {len(weekly_forecast)}日分")
            return weekly_forecast
            
        except Exception as e:
            logger.error(f"週間予報データの解析に失敗: {e}")
            return None
    
    def _get_weather_description_from_code(self, code):
        """天気コードから天気説明を取得"""
        weather_map = {
            '100': '晴れ', '101': '晴れ時々曇り', '102': '晴れ一時雨', '103': '晴れ時々雨',
            '104': '晴れ一時雪', '105': '晴れ時々雪', '106': '晴れ一時雨か雪', '107': '晴れ時々雨か雪',
            '108': '晴れ一時雨か雷雨', '110': '晴れ後時々曇り', '111': '晴れ後曇り',
            '112': '晴れ後一時雨', '113': '晴れ後時々雨', '114': '晴れ後雨',
            '115': '晴れ後一時雪', '116': '晴れ後時々雪', '117': '晴れ後雪',
            '118': '晴れ後雨か雪', '119': '晴れ後雨か雷雨', '120': '晴れ朝夕一時雨',
            '121': '晴れ朝の内一時雨', '122': '晴れ夕方一時雨', '123': '晴れ山沿い雷雨',
            '124': '晴れ山沿い雪', '125': '晴れ午後は雷雨', '126': '晴れ昼頃から雨',
            '127': '晴れ夕方から雨', '128': '晴れ夜は雨', '130': '朝の内霧後晴れ',
            '131': '晴れ明け方霧', '132': '晴れ朝夕曇り', '140': '晴れ時々雨と雷雨',
            '200': '曇り', '201': '曇り時々晴れ', '202': '曇り一時雨', '203': '曇り時々雨',
            '204': '曇り一時雪', '205': '曇り時々雪', '206': '曇り一時雨か雪', '207': '曇り時々雨か雪',
            '208': '曇り一時雨か雷雨', '209': '霧', '210': '曇り後時々晴れ', '211': '曇り後晴れ',
            '212': '曇り後一時雨', '213': '曇り後時々雨', '214': '曇り後雨',
            '215': '曇り後一時雪', '216': '曇り後時々雪', '217': '曇り後雪',
            '218': '曇り後雨か雪', '219': '曇り後雨か雷雨', '220': '曇り朝夕一時雨',
            '221': '曇り朝の内一時雨', '222': '曇り夕方一時雨', '223': '曇り日中時々晴れ',
            '224': '曇り昼頃から雨', '225': '曇り夕方から雨', '226': '曇り夜は雨',
            '228': '曇り昼頃から雪', '229': '曇り夕方から雪', '230': '曇り夜は雪',
            '231': '曇り海上海岸は霧か霧雨', '240': '曇り時々雨と雷雨', '250': '曇り時々雪と雷雨',
            '260': '曇り一時雪か雨', '270': '曇り時々雪か雨', '281': '曇り昼頃から雪か雨',
            '300': '雨', '301': '雨時々晴れ', '302': '雨時々止む', '303': '雨時々雪',
            '304': '雨か雪', '306': '大雨', '308': '雨で暴風を伴う', '309': '雨一時雪',
            '311': '雨後晴れ', '313': '雨後曇り', '314': '雨後時々雪', '315': '雨後雪',
            '316': '雨か雪後晴れ', '317': '雨か雪後曇り', '320': '朝の内雨後晴れ',
            '321': '朝の内雨後曇り', '322': '雨朝晩一時雪', '323': '雨昼頃から晴れ',
            '324': '雨夕方から晴れ', '325': '雨夜は晴', '326': '雨夕方から雪',
            '327': '雨夜は雪', '328': '雨一時強く降る', '329': '雨一時みぞれ',
            '340': '雪か雨', '350': '雨で雷を伴う', '361': '雪か雨後晴れ',
            '371': '雪か雨後曇り', '400': '雪', '401': '雪時々晴れ', '402': '雪時々止む',
            '403': '雪時々雨', '405': '大雪', '406': '風雪強い', '407': '暴風雪',
            '409': '雪一時雨', '411': '雪後晴れ', '413': '雪後曇り', '414': '雪後雨',
            '420': '朝の内雪後晴れ', '421': '朝の内雪後曇り', '422': '雪昼頃から晴れ',
            '423': '雪夕方から晴れ', '424': '雪夜は晴れ', '425': '雪一時強く降る',
            '426': '雪後みぞれ', '427': '雪一時みぞれ', '450': '雪で雷を伴う'
        }
        return weather_map.get(code, '不明')
    
    def get_weather_emoji(self, weather_code):
        """天気コードから絵文字アイコンを取得"""
        emoji_map = {
            # 晴れ系
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
            
            # 曇り系
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
            
            # 雨系
            '300': '🌧️', '301': '🌦️', '302': '🌧️', '303': '🌨️',
            '304': '🌨️', '306': '🌧️', '308': '🌪️', '309': '🌨️',
            '311': '🌦️', '313': '🌧️', '314': '🌨️', '315': '❄️',
            '316': '🌨️', '317': '🌨️', '320': '🌦️',
            '321': '🌧️', '322': '🌨️', '323': '🌦️',
            '324': '🌦️', '325': '🌧️', '326': '🌨️',
            '327': '❄️', '328': '🌧️', '329': '🌨️',
            '340': '🌨️', '350': '⛈️', '361': '🌨️',
            '371': '🌨️',
            
            # 雪系
            '400': '❄️', '401': '🌨️', '402': '❄️', '403': '🌨️',
            '405': '❄️', '406': '🌪️', '407': '🌪️',
            '409': '🌨️', '411': '🌨️', '413': '❄️', '414': '🌨️',
            '420': '🌨️', '421': '❄️', '422': '🌨️',
            '423': '🌨️', '424': '❄️', '425': '❄️',
            '426': '🌨️', '427': '🌨️', '450': '⛈️'
        }
        return emoji_map.get(weather_code, '🌈')
    
    def get_weather_icon_path(self, weather_code):
        """天気コードからローカル画像ファイルパスを取得"""
        # 基本的な天気パターンに分類
        if weather_code.startswith('1'):  # 晴れ系
            if weather_code in ['102', '103', '112', '113', '114', '119', '120', '121', '122', '125', '126', '127', '128', '140']:
                return 'assets/weather_icons/rainy.png'  # 晴れ後雨
            elif weather_code in ['104', '105', '115', '116', '117', '124']:
                return 'assets/weather_icons/snowy.png'  # 晴れ後雪
            elif weather_code in ['101', '110', '111', '132']:
                return 'assets/weather_icons/partly_cloudy.png'  # 晴れ時々曇り
            else:
                return 'assets/weather_icons/sunny.png'  # 晴れ
        
        elif weather_code.startswith('2'):  # 曇り系
            if weather_code in ['202', '203', '212', '213', '214', '219', '220', '221', '222', '224', '225', '226', '240']:
                return 'assets/weather_icons/rainy.png'  # 曇り後雨
            elif weather_code in ['204', '205', '215', '216', '217', '228', '229', '230', '250', '260', '270', '281']:
                return 'assets/weather_icons/snowy.png'  # 曇り後雪
            elif weather_code in ['201', '210', '211', '223']:
                return 'assets/weather_icons/partly_cloudy.png'  # 曇り時々晴れ
            else:
                return 'assets/weather_icons/cloudy.png'  # 曇り
        
        elif weather_code.startswith('3'):  # 雨系
            if weather_code in ['303', '309', '314', '315', '322', '326', '327', '329', '340', '361', '371']:
                return 'assets/weather_icons/snowy.png'  # 雨雪
            elif weather_code in ['306', '308', '328', '350']:
                return 'assets/weather_icons/storm.png'  # 大雨・暴風雨
            else:
                return 'assets/weather_icons/rainy.png'  # 雨
        
        elif weather_code.startswith('4'):  # 雪系
            if weather_code in ['405', '406', '407', '425', '450']:
                return 'assets/weather_icons/storm.png'  # 大雪・暴風雪
            else:
                return 'assets/weather_icons/snowy.png'  # 雪
        
        else:
            return 'assets/weather_icons/unknown.png'  # その他
    
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
    
    def _get_current_temperature_from_amedas(self):
        """気象庁overview_forecastAPIから現在気温を取得"""
        try:
            # overview_forecastエンドポイントのURL
            overview_url = f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{self.area_code}.json"
            
            response = requests.get(overview_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            overview_data = response.json()
            
            # 現在気温データの取得を試行
            if 'targetArea' in overview_data:
                target_area = overview_data['targetArea']
                # テキストから気温情報を抽出
                text = overview_data.get('text', '')
                
                # "現在の気温は○度"のようなパターンを探す
                import re
                temp_patterns = [
                    r'現在.*?気温.*?(\d+(?:\.\d+)?)度',
                    r'気温.*?(\d+(?:\.\d+)?)度',
                    r'(\d+(?:\.\d+)?)度.*?気温'
                ]
                
                for pattern in temp_patterns:
                    match = re.search(pattern, text)
                    if match:
                        temp = float(match.group(1))
                        logger.info(f"overview_forecast気温取得成功: {temp}°C (地域: {target_area})")
                        return temp
                
                logger.debug(f"overview_forecastテキスト: {text}")
            
            # overview_forecastで取得できない場合は、従来のアメダス方式を試行
            return self._get_current_temperature_from_amedas_fallback()
            
        except Exception as e:
            logger.error(f"overview_forecast気温取得エラー: {e}")
            # エラーの場合も従来方式にフォールバック
            return self._get_current_temperature_from_amedas_fallback()
    
    def _get_current_temperature_from_amedas_fallback(self):
        """アメダス実況データから現在気温を取得（フォールバック）"""
        try:
            from datetime import datetime, timedelta
            import json
            
            # 現在時刻の1時間前のデータを取得（実況データの更新頻度を考慮）
            now = datetime.now()
            target_time = now - timedelta(hours=1)
            date_str = target_time.strftime('%Y%m%d')
            hour_str = target_time.strftime('%H')
            
            # アメダス実況データのURL
            amedas_url = f"https://www.jma.go.jp/bosai/amedas/data/map/{date_str}{hour_str}0000.json"
            
            response = requests.get(amedas_url, timeout=10, verify=self.ssl_verify)
            response.raise_for_status()
            amedas_data = response.json()
            
            # 地域コードに対応するアメダス観測点を探す
            # 横浜: 46106, 千葉(銚子): 45148などから近い観測点を選択
            target_stations = {
                '140000': ['46106', '46078'],  # 神奈川県: 横浜、小田原
                '120000': ['45148', '45056']   # 千葉県: 銚子、木更津
            }
            
            stations_to_check = target_stations.get(self.area_code, [])
            
            # 該当観測点のデータを検索
            for station_id in stations_to_check:
                if station_id in amedas_data:
                    station_data = amedas_data[station_id]
                    if 'temp' in station_data and station_data['temp'][0] is not None:
                        temp = float(station_data['temp'][0])
                        logger.info(f"アメダス実況気温取得成功: {temp}°C (観測点: {station_id})")
                        return temp
            
            # 該当観測点がない場合は、首都圏の主要観測点を試行
            fallback_stations = ['44132', '44136', '46106', '45148']  # 東京、練馬、横浜、銚子
            for station_id in fallback_stations:
                if station_id in amedas_data:
                    station_data = amedas_data[station_id]
                    if 'temp' in station_data and station_data['temp'][0] is not None:
                        temp = float(station_data['temp'][0])
                        logger.info(f"アメダス実況気温取得成功(代替): {temp}°C (観測点: {station_id})")
                        return temp
            
            logger.warning("アメダス実況データから気温を取得できませんでした")
            return None
            
        except Exception as e:
            logger.error(f"アメダス実況データ取得エラー: {e}")
            return None
    
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
        
        result = {
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
        
        # 週間予報データがあれば追加
        if 'weekly_forecast' in weather_data:
            result['weekly_forecast'] = weather_data['weekly_forecast']
        
        return result
    
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
            
            # 週間予報データも含めて処理
            weekly_data = self._parse_weekly_forecast(forecast_data)
            weather_data = self._parse_weather_data(forecast_data)
            
            if weather_data and weekly_data:
                # 今日・明日予報から週間予報の最初の日を補完
                weekly_data = self._supplement_weekly_with_daily_forecast(forecast_data, weekly_data)
                weather_data['weekly_forecast'] = weekly_data
                
            return weather_data
            
        except Exception as e:
            logger.error(f"JSONファイルからのデータ読み込みエラー: {e}")
            return None