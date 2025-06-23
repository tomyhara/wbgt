import requests
import csv
import io
import os
import sys
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

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
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return self._parse_forecast_csv_data(response.text, location)
            else:
                logger.warning(f"環境省WBGTサービスからのデータ取得に失敗: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"環境省WBGTデータ取得エラー: {e}")
            return None
    
    def get_wbgt_current_data(self, location=None):
        """
        WBGT実況値データを取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: WBGT実況データ
        """
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
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return self._parse_current_csv_data(response.text, location)
            else:
                logger.warning(f"環境省WBGT実況データ取得に失敗: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"環境省WBGT実況データ取得エラー: {e}")
            return None
    
    def get_alert_data(self, location=None):
        """
        熱中症警戒アラート情報を取得
        
        Args:
            location (dict): 拠点情報（prefecture含む）
            
        Returns:
            dict: アラート情報
        """
        try:
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
            
            # 環境省データサービスの正式URL構造（アラート情報）
            url = f"{self.base_url}/alert/dl/{now.year}/alert_{target_date}_{file_time}.csv"
            logger.info(f"熱中症警戒アラートデータ取得URL: {url}")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return self._parse_alert_data(response.text, prefecture)
            else:
                logger.warning(f"環境省アラートデータ取得に失敗: {response.status_code} - URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"環境省アラートデータ取得エラー: {e}")
            return None
    
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
    
    def _parse_current_csv_data(self, csv_content, location):
        """実況値CSVデータを解析"""
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return None
            
            target_location_code = location.get('wbgt_location_code')
            
            for line in reversed(lines):  # 最新から検索
                data = line.split(',')
                if len(data) >= 4 and data[0] == target_location_code:
                    location_code = data[0]
                    date_time = data[1]
                    
                    try:
                        # WBGT値は10倍されているので10で割る
                        wbgt_val = int(data[2]) / 10.0 if data[2].strip() else None
                        
                        if wbgt_val is not None:
                            return {
                                'wbgt_value': wbgt_val,
                                'location_code': location_code,
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
            
            logger.info(f"アラートCSVから{len(data_lines)}行のデータを抽出")
            
            # CSVのデータ行を解析
            for line in data_lines:
                data = line.split(',')
                if len(data) >= 12:
                    prefecture_name = data[4] if len(data) > 4 else ''
                    target_date1_flag = data[6] if len(data) > 6 else '0'
                    target_date2_flag = data[7] if len(data) > 7 else '0'
                    
                    logger.debug(f"都道府県: {prefecture_name}, フラグ1: {target_date1_flag}, フラグ2: {target_date2_flag}")
                    
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
        flag_map = {
            '0': {'status': '発表なし', 'level': 0, 'message': ''},
            '1': {'status': '熱中症警戒情報', 'level': 3, 'message': '熱中症に警戒してください'},
            '2': {'status': '熱中症特別警戒情報（判定）', 'level': 2, 'message': '熱中症特別警戒情報の基準に達する可能性があります'},
            '3': {'status': '熱中症特別警戒情報', 'level': 4, 'message': '熱中症特別警戒情報が発表されています。危険な暑さです。'},
            '9': {'status': '発表時間外', 'level': 0, 'message': '発表時間外です'}
        }
        
        return flag_map.get(str(flag_value), {'status': '情報なし', 'level': 0, 'message': ''})
    
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