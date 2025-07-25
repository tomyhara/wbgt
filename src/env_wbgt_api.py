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

class EnvWBGTAPI:
    """
    環境省熱中症予防情報サイト WBGT データサービス クライアント
    
    環境省が提供する公式のWBGT指数データを取得します。
    https://www.wbgt.env.go.jp/data_service.php
    """
    
    def __init__(self):
        self.base_url = "https://www.wbgt.env.go.jp"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WBGT-Kiosk/1.0 (Heat Stroke Prevention System)'
        })
        
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
        
        # 都道府県名マッピング（環境省サービス用アルファベット表記）
        self.prefecture_names = {
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
        WBGT予測値データを取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: WBGT予測データ
        """
        # 強制CSV モードの確認
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("強制CSVモードが有効: CSVファイルからのデータ読み込みを試行中...")
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config import LOCATIONS
                location = LOCATIONS[0]
            return self._get_wbgt_forecast_from_csv(location)
        
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config import LOCATIONS
                location = LOCATIONS[0]
            
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # 環境省データサービスの正式URL構造（都道府県別予測値）
            url = f"{self.base_url}/prev15WG/dl/yohou_{pref_name}.csv"
            logger.info(f"WBGT予測値データ取得URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_forecast_csv_data(response.text, location)
            else:
                logger.warning(f"環境省WBGTサービスからのデータ取得に失敗: {response.status_code} - URL: {url}")
                return self._get_wbgt_forecast_from_csv(location)
                
        except Exception as e:
            logger.error(f"環境省WBGTデータ取得エラー: {e}")
            logger.info("CSVファイルからのWBGT予測データ読み込みを試行中...")
            return self._get_wbgt_forecast_from_csv(location)
    
    def get_wbgt_current_data(self, location=None):
        """
        WBGT実況値データを取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: WBGT実況データ
        """
        # 強制CSV モードの確認
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("強制CSVモードが有効: CSVファイルからのデータ読み込みを試行中...")
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config import LOCATIONS
                location = LOCATIONS[0]
            return self._get_wbgt_current_from_csv(location)
        
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config import LOCATIONS
                location = LOCATIONS[0]
                
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            now = datetime.now()
            year_month = f"{now.year}{now.month:02d}"
            
            # 環境省データサービスの正式URL構造（都道府県別実況値）
            url = f"{self.base_url}/est15WG/dl/wbgt_{pref_name}_{year_month}.csv"
            logger.info(f"WBGT実況値データ取得URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_current_csv_data(response.text, location)
            else:
                logger.warning(f"環境省WBGT実況データ取得に失敗: {response.status_code} - URL: {url}")
                return self._get_wbgt_current_from_csv(location)
                
        except Exception as e:
            logger.error(f"環境省WBGT実況データ取得エラー: {e}")
            logger.info("CSVファイルからのWBGT実況データ読み込みを試行中...")
            return self._get_wbgt_current_from_csv(location)
    
    def get_alert_data(self, location=None):
        """
        熱中症警戒アラート情報を取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: アラート情報
        """
        if location is None:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
            from config import LOCATIONS
            location = LOCATIONS[0]
            
        prefecture = location.get('prefecture')
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        
        # 時刻に応じて適切なファイルを選択
        if now.hour < 5:
            # 当日5時前は前日17時のファイル
            file_time = '17'
            target_date = (now - timedelta(days=1)).strftime('%Y%m%d')
        elif now.hour < 14:
            # 14時前は当日5時のファイル
            file_time = '05'
            target_date = date_str
        elif now.hour < 17:
            # 17時前は当日14時のファイル（特別警戒情報）
            file_time = '14'
            target_date = date_str
        else:
            # 17時以降は当日17時のファイル
            file_time = '17'
            target_date = date_str
        
        # 強制CSV モードの確認
        force_csv = os.environ.get('FORCE_CSV_MODE', '0') == '1'
        
        if force_csv:
            logger.info("強制CSVモードが有効: CSVファイルからのデータ読み込みを試行中...")
            return self._get_alert_from_csv(target_date, file_time, prefecture)
        
        try:
            # 環境省データサービスの正式URL構造（アラート情報）
            url = f"{self.base_url}/alert/dl/{now.year}/alert_{target_date}_{file_time}.csv"
            logger.info(f"熱中症警戒アラートデータ取得URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                csv_content = response.content.decode('utf-8')
                return self._parse_alert_data(csv_content, prefecture)
            else:
                logger.warning(f"環境省アラートデータ取得に失敗: {response.status_code} - URL: {url}")
                return self._get_alert_from_csv(target_date, file_time, prefecture)
                
        except Exception as e:
            logger.error(f"環境省アラートデータ取得エラー: {e}")
            logger.info("CSVファイルからのアラートデータ読み込みを試行中...")
            return self._get_alert_from_csv(target_date, file_time, prefecture)
    
    def _parse_forecast_csv_data(self, csv_content, location):
        """予測値CSVデータを解析"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # 2行目以降: 地点データ
            data_lines = lines[1:]
            target_location_code = location.get('wbgt_location_code')
            
            # 指定された地点のデータを検索
            for data_row_str in data_lines:
                data_row = data_row_str.split(',')
                if len(data_row) >= 3 and data_row[0] == target_location_code:
                    location_code = data_row[0]
                    update_time = data_row[1]
                    
                    # 最新の予測値を取得（3番目の要素から）
                    wbgt_values = []
                    for i in range(2, len(data_row)):
                        if data_row[i].strip():
                            try:
                                # WBGT値は10倍されているので10で割る
                                wbgt_val = int(data_row[i].strip()) / 10.0
                                wbgt_values.append(wbgt_val)
                            except (ValueError, TypeError):
                                continue
                    
                    if wbgt_values:
                        return {
                            'wbgt_value': wbgt_values[0],  # 最新の予測値
                            'location_code': location_code,
                            'location_name': location.get('name'),
                            'update_time': update_time,
                            'data_type': 'forecast',
                            'source': '環境省熱中症予防情報サイト（予測値）'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"予測値CSVデータ解析エラー: {e}")
            return None

    def get_wbgt_forecast_timeseries(self, location=None):
        """
        WBGT予測値の時系列データを取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: 時系列WBGT予測データ
        """
        try:
            if location is None:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
                from config import LOCATIONS
                location = LOCATIONS[0]
            
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # 環境省データサービスの正式URL構造（都道府県別予測値）
            url = f"{self.base_url}/prev15WG/dl/yohou_{pref_name}.csv"
            logger.info(f"WBGT予測値時系列データ取得URL: {url}")
            
            response = self.session.get(url, timeout=10, verify=self.ssl_verify)
            
            if response.status_code == 200:
                return self._parse_forecast_timeseries_csv_data(response.text, location)
            else:
                logger.warning(f"環境省WBGT時系列データ取得に失敗: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"環境省WBGT時系列データ取得エラー: {e}")
            return None

    def _parse_forecast_timeseries_csv_data(self, csv_content, location):
        """予測値時系列CSVデータを解析"""
        try:
            from datetime import datetime, timedelta
            
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # 1行目: 時刻ヘッダー
            time_headers = lines[0].split(',')[2:]  # 最初の2カラムはスキップ
            
            # 2行目以降: 地点データ
            data_lines = lines[1:]
            target_location_code = location.get('wbgt_location_code')
            
            # 指定された地点のデータを検索
            for data_row_str in data_lines:
                data_row = data_row_str.split(',')
                if len(data_row) >= 3 and data_row[0] == target_location_code:
                    location_code = data_row[0]
                    update_time = data_row[1]
                    
                    # 時系列データを作成
                    timeseries_data = []
                    for i, time_str in enumerate(time_headers):
                        if i + 2 < len(data_row) and data_row[i + 2].strip():
                            try:
                                # WBGT値は10倍されているので10で割る
                                wbgt_val = int(data_row[i + 2].strip()) / 10.0
                                
                                # 時刻文字列を解析 (YYYYMMDDHH形式)
                                if len(time_str.strip()) == 10:
                                    year = int(time_str[0:4])
                                    month = int(time_str[4:6])
                                    day = int(time_str[6:8])
                                    hour = int(time_str[8:10])
                                    
                                    # 24時を0時に変換
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
                                logger.debug(f"時系列データ解析エラー (時刻: {time_str}): {e}")
                                continue
                    
                    if timeseries_data:
                        return {
                            'location_code': location_code,
                            'location_name': location.get('name'),
                            'update_time': update_time,
                            'timeseries': timeseries_data,
                            'data_type': 'forecast_timeseries',
                            'source': '環境省熱中症予防情報サイト（予測値時系列）'
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"予測値時系列CSVデータ解析エラー: {e}")
            return None
    
    def _parse_current_csv_data(self, csv_content, location):
        """実況値CSVデータを解析"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            target_location_code = location.get('wbgt_location_code')
            
            # ヘッダー行から地点番号のインデックスを取得
            header = lines[0].split(',')
            target_column_index = -1
            
            for i, column_name in enumerate(header):
                if column_name.strip() == target_location_code:
                    target_column_index = i
                    break
            
            if target_column_index == -1:
                logger.warning(f"地点番号 {target_location_code} がヘッダーに見つかりません: {header}")
                return None
            
            # 最新のデータ行から検索（下から上へ）
            for line in reversed(lines[1:]):  # ヘッダー行をスキップ
                data = line.split(',')
                if len(data) > target_column_index:
                    date_time = f"{data[0]} {data[1]}" if len(data) > 1 else data[0]
                    
                    try:
                        # 実況値は10で割る必要がない（既に実際の値）
                        wbgt_val = float(data[target_column_index]) if data[target_column_index].strip() else None
                        
                        if wbgt_val is not None:
                            return {
                                'wbgt_value': wbgt_val,
                                'location_code': target_location_code,
                                'location_name': location.get('name'),
                                'datetime': date_time,
                                'data_type': 'current',
                                'source': '環境省熱中症予防情報サイト（実況値）'
                            }
                    except (ValueError, TypeError):
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"実況値CSVデータ解析エラー: {e}")
            return None
    
    def _parse_alert_data(self, csv_content, target_prefecture):
        """アラートデータを解析"""
        try:
            lines = csv_content.strip().split('\n')
            if not lines:
                return None
            
            alerts = {
                'today': {'status': '発表なし', 'level': 0, 'message': ''},
                'tomorrow': {'status': '発表なし', 'level': 0, 'message': ''}
            }
            
            # メタデータを除いてデータ行のみ処理
            data_lines = []
            for line in lines:
                # メタデータ行をスキップ（Title, Encoding, TimeZoneなど）
                # 都道府県データ行は含める（カンマ区切りで12項目以上あり、数字で始まらないもの）
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
                    len(line.split(',')) >= 8):  # 都道府県データ行は最低8項目以上
                    data_lines.append(line)
                    logger.debug(f"データ行として追加: {line[:50]}...")
            
            logger.info(f"アラートCSVから{len(data_lines)}行のデータを抽出")
            
            # CSVのデータ行を解析
            for line in data_lines:
                data = line.split(',')
                if len(data) >= 8:  # 都道府県データ行は最低8項目以上
                    prefecture_name = data[4] if len(data) > 4 else ''
                    target_date1_flag = data[6] if len(data) > 6 else '0'
                    target_date2_flag = data[7] if len(data) > 7 else '0'
                    
                    logger.debug(f"都道府県: {prefecture_name}, フラグ1: {target_date1_flag}, フラグ2: {target_date2_flag}")
                    logger.debug(f"target_prefecture='{target_prefecture}', prefecture_name='{prefecture_name}'")
                    logger.debug(f"target_short='{target_prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', '')}'")
                    
                    # 対象都道府県のデータを検索（都道府県名の部分一致）
                    target_short = target_prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', '')
                    if (target_short in prefecture_name or 
                        prefecture_name in target_short or 
                        target_prefecture == prefecture_name):
                        
                        logger.info(f"対象都道府県 {target_prefecture} のデータを発見: {prefecture_name}")
                        
                        # TargetDate1フラグ（今日）の処理
                        alerts['today'] = self._parse_alert_flag(target_date1_flag)
                        
                        # TargetDate2フラグ（明日）の処理  
                        alerts['tomorrow'] = self._parse_alert_flag(target_date2_flag)
                        break
            
            return {
                'prefecture': target_prefecture,
                'alerts': alerts,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '環境省熱中症予防情報サイト（公式アラート）'
            }
            
        except Exception as e:
            logger.error(f"アラートデータ解析エラー: {e}")
            return None
    
    def _parse_alert_flag(self, flag_value):
        """アラートフラグを解析"""
        logger.debug(f"アラートフラグ解析: flag_value='{flag_value}' (type: {type(flag_value)})")
        
        flag_map = {
            '0': {'status': '発表なし', 'level': 0, 'message': ''},
            '1': {'status': '熱中症警戒情報', 'level': 3, 'message': '熱中症に警戒してください'},
            '2': {'status': '熱中症特別警戒情報（判定）', 'level': 2, 'message': '熱中症特別警戒情報の基準に達する可能性があります'},
            '3': {'status': '熱中症特別警戒情報', 'level': 4, 'message': '熱中症特別警戒情報が発表されています。危険な暑さです。'},
            '9': {'status': '発表時間外', 'level': 0, 'message': '発表時間外です'}
        }
        
        result = flag_map.get(str(flag_value), {'status': '情報なし', 'level': 0, 'message': ''})
        logger.debug(f"アラートフラグ解析結果: {result}")
        return result
    
    def _get_alert_numeric_level(self, alert_level):
        """アラートレベルを数値に変換"""
        level_map = {
            '熱中症特別警戒情報': 4,
            '熱中症警戒情報': 3,
            '熱中症特別警戒情報（判定）': 2,
            '発表なし': 0,
            '発表時間外': 0,
            '情報なし': 0
        }
        return level_map.get(alert_level, 0)
    
    def get_wbgt_level_info(self, wbgt_value):
        """
        WBGT値から警戒レベル情報を取得
        環境省の基準に基づく
        """
        if wbgt_value >= 31:
            return "危険", "red", "外出は避け、涼しい室内に移動する"
        elif wbgt_value >= 28:
            return "厳重警戒", "orange", "外出時は炎天下を避け、室内では空調を適切に"
        elif wbgt_value >= 25:
            return "警戒", "yellow", "運動や激しい作業をする際は定期的に充分に休息"
        elif wbgt_value >= 21:
            return "注意", "green", "一般に危険性は少ないが激しい運動や重労働時には発生する危険性"
        else:
            return "ほぼ安全", "blue", "通常は熱中症の危険は小さい"
    
    def is_service_available(self):
        """
        環境省WBGTサービスが利用可能かチェック
        サービス期間: 4月下旬～10月下旬
        """
        now = datetime.now()
        year = now.year
        
        # サービス期間の確認（4月23日～10月22日）
        service_start = datetime(year, 4, 23)
        service_end = datetime(year, 10, 22)
        
        # テスト用：現在の期間を強制的に有効として扱う（実装テスト用）
        # 実際の運用では以下のコメントアウトを外してください
        return True  # return service_start <= now <= service_end
    
    def _get_wbgt_forecast_from_csv(self, location):
        """CSVファイルからWBGT予測データを取得（APIアクセス失敗時のフォールバック）"""
        try:
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            
            # CSVファイルのパスを構築
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'wbgt_forecast_{pref_name}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"WBGT予測CSVファイルが見つかりません: {csv_file}")
                return None
            
            # ファイルの更新時間をチェック（24時間以内かどうか）
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24時間
                logger.warning(f"WBGT予測CSVファイルが古すぎます（{(current_time - file_mtime) / 3600:.1f}時間前）")
                return None
            
            # CSVファイルを読み込み
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"CSVファイルからWBGT予測データを正常に読み込みました: {csv_file}")
            return self._parse_forecast_csv_data(csv_content, location)
            
        except Exception as e:
            logger.error(f"CSVファイルからのWBGT予測データ読み込みエラー: {e}")
            return None
    
    def _get_wbgt_current_from_csv(self, location):
        """CSVファイルからWBGT実況データを取得（APIアクセス失敗時のフォールバック）"""
        try:
            prefecture = location.get('prefecture')
            pref_name = self.prefecture_names.get(prefecture, 'kanagawa')
            now = datetime.now()
            year_month = f"{now.year}{now.month:02d}"
            
            # CSVファイルのパスを構築
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'wbgt_current_{pref_name}_{year_month}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"WBGT実況CSVファイルが見つかりません: {csv_file}")
                return None
            
            # ファイルの更新時間をチェック（6時間以内かどうか）
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 6 * 3600:  # 6時間
                logger.warning(f"WBGT実況CSVファイルが古すぎます（{(current_time - file_mtime) / 3600:.1f}時間前）")
                return None
            
            # CSVファイルを読み込み
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"CSVファイルからWBGT実況データを正常に読み込みました: {csv_file}")
            return self._parse_current_csv_data(csv_content, location)
            
        except Exception as e:
            logger.error(f"CSVファイルからのWBGT実況データ読み込みエラー: {e}")
            return None
    
    def _get_alert_from_csv(self, target_date, file_time, prefecture):
        """CSVファイルからアラートデータを取得（APIアクセス失敗時のフォールバック）"""
        try:
            # CSVファイルのパスを構築
            script_dir = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(script_dir, 'data', 'csv', f'alert_{target_date}_{file_time}.csv')
            
            if not os.path.exists(csv_file):
                logger.warning(f"アラートCSVファイルが見つかりません: {csv_file}")
                return None
            
            # ファイルの更新時間をチェック（24時間以内かどうか）
            file_mtime = os.path.getmtime(csv_file)
            current_time = datetime.now().timestamp()
            if current_time - file_mtime > 24 * 3600:  # 24時間
                logger.warning(f"アラートCSVファイルが古すぎます（{(current_time - file_mtime) / 3600:.1f}時間前）")
                return None
            
            # CSVファイルを読み込み
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            logger.info(f"CSVファイルからアラートデータを正常に読み込みました: {csv_file}")
            return self._parse_alert_data(csv_content, prefecture)
            
        except Exception as e:
            logger.error(f"CSVファイルからのアラートデータ読み込みエラー: {e}")
            return None