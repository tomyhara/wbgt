#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WBGT熱中症警戒キオスク
Raspberry Pi用熱中症警戒アラート情報と天気を表示するキオスク端末

Usage:
    python3 wbgt_kiosk.py [--demo] [--gui]
    
Options:
    --demo    短時間デモモード（3回更新して終了）
    --gui     GUI版で起動（実験的）
    デフォルト: ターミナル版で起動
"""
import os
import sys

# Windows での Unicode 出力エラーを防ぐための設定
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time
import signal
import argparse
from datetime import datetime
import threading
import logging

# 設定の読み込み (JSON設定を使用)
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
    from config_loader import load_config
    config_data = load_config()
    
    # 後方互換性のため、古い変数名も設定
    class Config:
        def __init__(self, config_dict):
            self._config = config_dict
            # 旧形式の変数名でアクセス可能にする
            self.LOCATIONS = config_dict.get('locations', [])
            self.AREA_CODES = config_dict.get('area_codes', {})
            self.UPDATE_INTERVAL_MINUTES = config_dict.get('update_interval_minutes', 30)
            self.DISPLAY_WIDTH = config_dict.get('display', {}).get('width', 800)
            self.DISPLAY_HEIGHT = config_dict.get('display', {}).get('height', 600)
            self.FULLSCREEN = config_dict.get('display', {}).get('fullscreen', False)
            self.FONT_SIZE_LARGE = config_dict.get('font_sizes', {}).get('large', 24)
            self.FONT_SIZE_MEDIUM = config_dict.get('font_sizes', {}).get('medium', 18)
            self.FONT_SIZE_SMALL = config_dict.get('font_sizes', {}).get('small', 14)
            self.LOG_LEVEL = config_dict.get('logging', {}).get('level', 'INFO')
            self.LOG_FILE = config_dict.get('logging', {}).get('file', 'wbgt_kiosk.log')
            
            # 旧形式で最初の地点を使用（後方互換性）
            if self.LOCATIONS:
                first_location = self.LOCATIONS[0]
                self.AREA_CODE = first_location.get('area_code', '130000')
                self.CITY_NAME = first_location.get('name', '東京')
            else:
                self.AREA_CODE = '130000'
                self.CITY_NAME = '東京'
    
    config = Config(config_data)
    
except Exception as e:
    print(f"❌ 設定ファイルの読み込みエラー: {e}")
    print("📝 setup/config.json を確認してください。")
    sys.exit(1)

# JSONコンフィグから読み込み済み（デフォルト値設定不要）

from jma_api import JMAWeatherAPI
from heatstroke_alert import HeatstrokeAlert
from env_wbgt_api import EnvWBGTAPI

class WBGTKiosk:
    """WBGT熱中症警戒キオスクのメインクラス"""
    
    def __init__(self, demo_mode=False, gui_mode=False):
        self.demo_mode = demo_mode
        self.gui_mode = gui_mode
        self.locations = config.LOCATIONS
        self.weather_apis = [JMAWeatherAPI(area_code=loc['area_code']) for loc in self.locations]
        self.heatstroke_alert = HeatstrokeAlert()
        self.env_wbgt_api = EnvWBGTAPI()
        self.locations_data = []
        self.running = True
        self.demo_count = 0
        
        # ログ設定
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def setup_logging(self):
        """ログの設定"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
            format=log_format,
            handlers=[
                logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def signal_handler(self, signum, frame):
        """Ctrl+Cでの終了処理"""
        print("\n\n👋 キオスクを終了します")
        self.running = False
        self.logger.info("ユーザーによってアプリケーションが終了されました")
        sys.exit(0)
    
    def clear_screen(self):
        """画面をクリア"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_color_code(self, color_name):
        """ANSI色コードを取得（Windows互換）"""
        # Windows環境では色コードを無効化
        import platform
        if platform.system() == 'Windows':
            return ''
        
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'gray': '\033[90m',
            'orange': '\033[93m',
            'darkred': '\033[91m',
            'reset': '\033[0m'
        }
        return colors.get(color_name, colors['white'])
    
    def colored_text(self, text, color):
        """色付きテキスト"""
        if self.gui_mode:
            return text  # GUI版では色コードを使用しない
        color_code = self.get_color_code(color)
        reset_code = self.get_color_code('reset')
        return f"{color_code}{text}{reset_code}"
    
    def update_data(self):
        """複数拠点のデータを更新"""
        try:
            self.logger.info("データ更新開始")
            if not self.demo_mode:
                print("📡 データ取得中...")
            
            self.locations_data = []
            
            for i, location in enumerate(self.locations):
                location_data = {
                    'location': location,
                    'weather_data': None,
                    'alert_data': None,
                    'env_wbgt_data': None
                }
                
                # 気象庁APIからデータ取得
                location_data['weather_data'] = self.weather_apis[i].get_weather_data()
                location_data['alert_data'] = self.heatstroke_alert.get_alert_data(location.get('prefecture', '東京都'))
                
                # 環境省WBGTサービスからデータ取得（サービス期間内の場合）
                if self.env_wbgt_api.is_service_available():
                    # 実況値と予測値の両方を取得
                    current_data = self.env_wbgt_api.get_wbgt_current_data(location)
                    forecast_data = self.env_wbgt_api.get_wbgt_forecast_data(location)
                    
                    # GUI版の場合は時系列データも取得
                    if self.gui_mode:
                        forecast_timeseries = self.env_wbgt_api.get_wbgt_forecast_timeseries(location)
                        location_data['env_wbgt_timeseries'] = forecast_timeseries
                    
                    # 両方のデータを保持
                    location_data['env_wbgt_current'] = current_data
                    location_data['env_wbgt_forecast'] = forecast_data
                    
                    # 表示用のメインデータを決定（実況値を優先）
                    if current_data:
                        location_data['env_wbgt_data'] = current_data
                    elif forecast_data:
                        location_data['env_wbgt_data'] = forecast_data
                    
                    if location_data['env_wbgt_data']:
                        # 環境省の公式データがある場合は優先使用
                        self._integrate_env_wbgt_data(location_data)
                        if not self.demo_mode:
                            data_types = []
                            if current_data:
                                data_types.append('実況値')
                            if forecast_data:
                                data_types.append('予測値')
                            print(self.colored_text(f"✅ {location['name']} 環境省公式WBGTデータ取得完了 ({'/'.join(data_types)})", 'green'))
                
                self.locations_data.append(location_data)
            
            if not self.demo_mode:
                print(self.colored_text("✅ 全拠点データ取得完了", 'green'))
            
            self.logger.info("データ更新完了")
            return True
            
        except Exception as e:
            self.logger.error(f"データ更新エラー: {e}")
            if not self.demo_mode:
                print(self.colored_text(f"❌ データ取得エラー: {e}", 'red'))
            return False
    
    def _integrate_env_wbgt_data(self, location_data):
        """環境省WBGTデータを気象庁データと統合"""
        if location_data['env_wbgt_data'] and location_data['weather_data']:
            # 環境省の公式WBGT値を使用
            official_wbgt = location_data['env_wbgt_data']['wbgt_value']
            level, color, advice = self.env_wbgt_api.get_wbgt_level_info(official_wbgt)
            
            # 既存の天気データを更新
            location_data['weather_data'].update({
                'wbgt': official_wbgt,
                'wbgt_level': level,
                'wbgt_color': color,
                'wbgt_advice': advice,
                'wbgt_source': '環境省公式データ'
            })
            
            location_name = location_data['location']['name']
            self.logger.info(f"{location_name} 環境省公式WBGT値を使用: {official_wbgt}°C")
    
    def display_header(self):
        """ヘッダーを表示"""
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        mode_text = "デモモード" if self.demo_mode else "運用モード"
        
        print("=" * 120)
        print(self.colored_text("           🌡️  WBGT熱中症警戒キオスク（複数拠点対応）  🌡️", 'cyan'))
        print("=" * 120)
        print(f"現在時刻: {self.colored_text(current_time, 'white')}")
        location_names = [loc['name'] for loc in self.locations]
        print(f"監視拠点: {self.colored_text(' / '.join(location_names), 'cyan')}")
        if self.demo_mode:
            print(f"モード: {self.colored_text(mode_text, 'yellow')} ({self.demo_count + 1}/3)")
        print("-" * 120)
    
    def display_weather(self, location_data):
        """天気情報を表示"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data:
            print(self.colored_text(f"❌ {location_name} 天気データを取得できませんでした", 'red'))
            return
        
        # 天気アイコンを取得
        weather_code = weather_data.get('weather_code', '100')
        weather_api = self.weather_apis[0]  # 最初のAPIインスタンスを使用
        weather_emoji = weather_api.get_weather_emoji(weather_code)
        
        print(self.colored_text(f"{weather_emoji}  {location_name} - 現在の天気情報", 'cyan'))
        print("-" * 50)
        
        temp_text = f"{weather_data.get('temperature', 'N/A')}°C"
        humidity_text = f"{weather_data.get('humidity', 'N/A')}%"
        feels_like_text = f"{weather_data.get('feels_like', 'N/A')}°C"
        
        print(f"湿度: {self.colored_text(humidity_text, 'blue')}  天気: {weather_emoji} {self.colored_text(weather_data.get('weather_description', 'Unknown'), 'green')}")
    
    def display_wbgt(self, location_data):
        """WBGT情報を表示"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data:
            return
        
        wbgt_color = weather_data['wbgt_color']
        
        print(self.colored_text(f"🌡️  {location_name} - WBGT指数（熱中症指数）", 'cyan'))
        print("-" * 50)
        
        wbgt_text = f"{weather_data.get('wbgt', 'N/A')}°C"
        level_text = f"({weather_data.get('wbgt_level', 'Unknown')})"
        
        print(f"WBGT指数: {self.colored_text(wbgt_text, wbgt_color)} " + 
              self.colored_text(level_text, wbgt_color))
        
        # 環境省データの実況値と予測値を両方表示
        current_data = location_data.get('env_wbgt_current')
        forecast_data = location_data.get('env_wbgt_forecast')
        
        if current_data or forecast_data:
            print(f"📊 環境省公式データ:")
            if current_data:
                current_level, current_color, _ = self.env_wbgt_api.get_wbgt_level_info(current_data['wbgt_value'])
                wbgt_val = current_data.get('wbgt_value', 'N/A')
                print(f"   実況値: {self.colored_text(f'{wbgt_val}°C', current_color)} " +
                      f"({self.colored_text(current_level, current_color)})")
                if 'datetime' in current_data:
                    print(f"   更新時刻: {current_data.get('datetime', 'Unknown')}")
            if forecast_data:
                forecast_level, forecast_color, _ = self.env_wbgt_api.get_wbgt_level_info(forecast_data['wbgt_value'])
                forecast_val = forecast_data.get('wbgt_value', 'N/A')
                print(f"   予測値: {self.colored_text(f'{forecast_val}°C', forecast_color)} " +
                      f"({self.colored_text(forecast_level, forecast_color)})")
                if 'update_time' in forecast_data:
                    print(f"   更新時刻: {forecast_data.get('update_time', 'Unknown')}")
        
        # データソース表示
        if 'wbgt_source' in weather_data:
            source_color = 'green' if '環境省' in weather_data['wbgt_source'] else 'yellow'
            print(f"データソース: {self.colored_text(weather_data.get('wbgt_source', 'Unknown'), source_color)}")
        else:
            print(f"データソース: {self.colored_text('気象庁API（計算値）', 'yellow')}")
        
        print(f"📋 アドバイス: {self.colored_text(weather_data.get('wbgt_advice', 'データなし'), 'white')}")
        
        # WBGT レベル表示
        level = weather_data['wbgt_level']
        if level == "極めて危険" or level == "危険":
            indicator = "🚨🚨🚨 危険 🚨🚨🚨"
        elif level == "厳重警戒":
            indicator = "⚠️⚠️ 厳重警戒 ⚠️⚠️"
        elif level == "警戒":
            indicator = "⚠️ 警戒 ⚠️"
        elif level == "注意":
            indicator = "⚠️ 注意"
        else:
            indicator = "✅ ほぼ安全"
        
        print(f"レベル: {self.colored_text(indicator, wbgt_color)}")
        print()
    
    def display_alerts(self, location_data):
        """熱中症警戒アラートを表示"""
        alert_data = location_data['alert_data']
        location_name = location_data['location']['name']
        
        if not alert_data:
            print(self.colored_text(f"❌ {location_name} アラートデータを取得できませんでした", 'red'))
            return
        
        print(self.colored_text(f"🚨 {location_name} - 熱中症警戒アラート", 'cyan'))
        print("-" * 50)
        
        today_alert = alert_data['alerts']['today']
        tomorrow_alert = alert_data['alerts']['tomorrow']
        
        today_color = self.heatstroke_alert.get_alert_color(today_alert['level'])
        tomorrow_color = self.heatstroke_alert.get_alert_color(tomorrow_alert['level'])
        
        print(f"今日:   {self.colored_text(today_alert.get('status', 'Unknown'), today_color)}")
        if today_alert['message']:
            print(f"        {today_alert.get('message', '')}")
        
        print(f"明日:   {self.colored_text(tomorrow_alert.get('status', 'Unknown'), tomorrow_color)}")
        if tomorrow_alert['message']:
            print(f"        {tomorrow_alert.get('message', '')}")
        print()
    
    def display_weekly_forecast(self, location_data):
        """週間予報を表示"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data or 'weekly_forecast' not in weather_data:
            return
        
        weekly_forecast = weather_data['weekly_forecast']
        if not weekly_forecast:
            return
        
        # コンパクトな1列表示
        forecast_items = []
        weather_api = self.weather_apis[0]  # 最初のAPIインスタンスを使用
        for day in weekly_forecast[:7]:  # 最大7日間
            date_str = day['date']
            weekday = day['weekday']
            weather_desc = day['weather_desc'][:4] if day['weather_desc'] else '--'  # 天気説明をさらに短縮
            pop = day['pop'] if day['pop'] is not None and day['pop'] != '' else '予報なし'
            temp_max = day['temp_max'] if day['temp_max'] is not None and day['temp_max'] != '' else '予報なし'
            temp_min = day['temp_min'] if day['temp_min'] is not None and day['temp_min'] != '' else '予報なし'
            
            # 天気アイコンを取得
            weather_code = day.get('weather_code', '100')
            weather_emoji = weather_api.get_weather_emoji(weather_code)
            
            # 降水確率に応じた色付け
            pop_color = 'blue'
            if pop != '予報なし':
                try:
                    pop_val = int(pop)
                    if pop_val >= 70:
                        pop_color = 'red'
                    elif pop_val >= 50:
                        pop_color = 'yellow'
                    elif pop_val >= 30:
                        pop_color = 'orange'
                except:
                    pass
            
            # 気温に応じた色付け
            temp_max_color = 'yellow'
            if temp_max != '予報なし':
                try:
                    temp_val = int(temp_max)
                    if temp_val >= 35:
                        temp_max_color = 'red'
                    elif temp_val >= 30:
                        temp_max_color = 'orange'
                except:
                    pass
            
            # コンパクトなフォーマット: 日付(曜) 絵文字 天気 降水% 最高/最低°
            pop_display = f'{pop}%' if pop != '予報なし' else '予報なし'
            temp_max_display = f'{temp_max}' if temp_max != '予報なし' else '予報なし'
            temp_min_display = f'{temp_min}' if temp_min != '予報なし' else '予報なし'
            item = f"{date_str}({weekday}) {weather_emoji} {self.colored_text(pop_display, pop_color)} {self.colored_text(temp_max_display, temp_max_color)}/{temp_min_display}°"
            forecast_items.append(item)
        
        # 1列に連結して表示
        forecast_line = " | ".join(forecast_items)
        print(self.colored_text(f"📅 {location_name}", 'cyan') + f": {forecast_line}")
    
    def display_footer(self):
        """フッターを表示"""
        if self.locations_data and self.locations_data[0]['weather_data']:
            update_time = self.locations_data[0]['weather_data']['timestamp']
            print(f"最終更新: {self.colored_text(update_time, 'gray')}")
        
        if self.demo_mode:
            if self.demo_count < 2:
                print(self.colored_text("5秒後に再更新します...", 'gray'))
            else:
                print(self.colored_text("デモ完了！", 'green'))
        else:
            interval = config.UPDATE_INTERVAL_MINUTES
            print(self.colored_text(f"Ctrl+C で終了 | {interval}分ごとに自動更新", 'gray'))
        
        print("=" * 120)
    
    def display_all(self):
        """全体表示"""
        self.clear_screen()
        self.display_header()
        
        # 各拠点の情報を横並びで表示
        for i, location_data in enumerate(self.locations_data):
            if i > 0:
                print("\n" + "=" * 120 + "\n")
            
            self.display_weather(location_data)
            self.display_wbgt(location_data)
            self.display_alerts(location_data)
            self.display_weekly_forecast(location_data)
        
        self.display_footer()
    
    def run_demo_mode(self):
        """デモモード実行"""
        print(self.colored_text("🚀 WBGT熱中症警戒キオスク デモモード", 'cyan'))
        print()
        print("📝 このデモは自動で以下を確認します:")
        print("  ✅ 気象庁APIからの天気データ取得")
        print("  ✅ WBGT指数の計算と表示")
        print("  ✅ 熱中症警戒レベルの判定")
        print("  ✅ 色付きターミナル表示")
        print()
        print("⏱️ 3回データ更新してから終了します")
        print()
        
        # 3秒後に開始
        for i in range(3, 0, -1):
            print(f"デモ開始まで {i} 秒...")
            time.sleep(1)
        
        try:
            for self.demo_count in range(3):
                print(f"\n=== デモ {self.demo_count + 1}/3 ===")
                
                if self.update_data():
                    time.sleep(1)
                    self.display_all()
                else:
                    print(self.colored_text("⚠️ データ取得に失敗しました", 'yellow'))
                
                if self.demo_count < 2:
                    for i in range(5, 0, -1):
                        print(f"\r次の更新まで {i} 秒...   ", end='', flush=True)
                        time.sleep(1)
                    print()
            
            print("\n" + "=" * 80)
            print(self.colored_text("🎉 デモ完了！WBGTキオスクが正常に動作しています。", 'green'))
            print()
            print("📱 本格運用する場合は以下のコマンドを使用してください:")
            print(f"   {self.colored_text('./run_wbgt.sh', 'cyan')}")
            print("=" * 80)
                
        except KeyboardInterrupt:
            print("\n\n👋 デモを中断しました")
    
    def run_terminal_mode(self):
        """ターミナルモード実行"""
        self.logger.info("ターミナルキオスクアプリケーション開始")
        
        print(self.colored_text("WBGT熱中症警戒キオスク起動中...", 'cyan'))
        print("初回データ取得中...")
        
        # 初回データ取得
        if self.update_data():
            print(self.colored_text("✅ 初期化完了", 'green'))
        else:
            print(self.colored_text("⚠️ 初期データ取得に問題がありますが、継続します", 'yellow'))
        
        time.sleep(1)
        
        try:
            while self.running:
                # データ更新と表示
                self.update_data()
                self.display_all()
                
                # 更新間隔まで待機
                interval_seconds = config.UPDATE_INTERVAL_MINUTES * 60
                for i in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.clear_screen()
            print(self.colored_text("WBGT熱中症警戒キオスクを終了しました", 'cyan'))
            self.logger.info("ターミナルキオスクアプリケーション終了")
    
    def run_gui_mode(self):
        """キオスク用GUI モード実行"""
        try:
            import tkinter as tk
            from tkinter import ttk
            from datetime import datetime
            import os
            
            # macOS環境でのGUI表示確認
            if os.environ.get('DISPLAY') is None and 'Darwin' in os.uname().sysname:
                print("🪟 WBGT熱中症警戒キオスク GUI版を起動中...")
                print("⚠️  macOS環境でのGUI起動を試行中...")
            
            print("✅ GUI準備完了")
            
            # メインウィンドウ設定
            root = tk.Tk()
            root.title("WBGT熱中症警戒キオスク（複数拠点対応）")
            root.geometry(f"{config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT}")
            root.configure(bg='#1a1a1a')
            
            if config.FULLSCREEN:
                root.attributes('-fullscreen', True)
                root.bind('<Escape>', lambda e: root.destroy())
            
            # フォント設定
            header_font = ('Helvetica', config.FONT_SIZE_LARGE, 'bold')
            title_font = ('Helvetica', config.FONT_SIZE_MEDIUM, 'bold')
            data_font = ('Helvetica', config.FONT_SIZE_SMALL)
            
            # メインフレーム
            main_frame = tk.Frame(root, bg='#1a1a1a')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # ヘッダー
            header_frame = tk.Frame(main_frame, bg='#1a1a1a')
            header_frame.pack(fill=tk.X, pady=(0, 20))
            
            title_label = tk.Label(header_frame, 
                                 text="🌡️ WBGT熱中症警戒キオスク（複数拠点対応） 🌡️",
                                 font=header_font, fg='#00ccff', bg='#1a1a1a')
            title_label.pack()
            
            time_label = tk.Label(header_frame, text="", font=data_font, fg='white', bg='#1a1a1a')
            time_label.pack()
            
            locations_label = tk.Label(header_frame, text="", font=data_font, fg='#00ccff', bg='#1a1a1a')
            locations_label.pack()
            
            # 拠点表示フレーム（2列レイアウト）
            locations_frame = tk.Frame(main_frame, bg='#1a1a1a')
            locations_frame.pack(fill=tk.BOTH, expand=True)
            
            
            # 拠点情報フレームを再構築（2列レイアウト）
            location_frames = []
            for i, location in enumerate(self.locations):
                col = i % 2
                location_frame = tk.Frame(locations_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
                location_frame.grid(row=0, column=col, sticky='nsew', padx=10, pady=10)
                locations_frame.grid_columnconfigure(col, weight=1, uniform='location')
                locations_frame.grid_rowconfigure(0, weight=1)
                
                # 拠点名
                location_title = tk.Label(location_frame, 
                                        text=f"📍 {location.get('name', 'Unknown')}",
                                        font=title_font, fg='#00ccff', bg='#2a2a2a')
                location_title.pack(pady=10)
                
                # 天気情報フレーム
                weather_frame = tk.LabelFrame(location_frame, text="🌤️ 天気情報", 
                                            font=data_font, fg='#00ccff', bg='#2a2a2a')
                weather_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # 天気アイコンと説明を表示するフレーム
                weather_info_frame = tk.Frame(weather_frame, bg='#2a2a2a')
                weather_info_frame.pack(anchor='w', fill='x')
                
                weather_icon_label = tk.Label(weather_info_frame, text="", font=('Arial', 20), fg='white', bg='#2a2a2a')
                weather_icon_label.pack(side='left')
                
                weather_desc_label = tk.Label(weather_info_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                weather_desc_label.pack(side='left', padx=(5, 0))
                
                
                # 予想気温フレーム（最低気温と最高気温を色分け表示）
                forecast_temp_frame = tk.Frame(weather_frame, bg='#2a2a2a')
                forecast_temp_frame.pack(anchor='w', fill='x')
                
                forecast_label = tk.Label(forecast_temp_frame, text="予想気温: ", font=data_font, fg='white', bg='#2a2a2a')
                forecast_label.pack(side='left')
                
                forecast_low_label = tk.Label(forecast_temp_frame, text="", font=data_font, fg='lightblue', bg='#2a2a2a')
                forecast_low_label.pack(side='left')
                
                forecast_dash_label = tk.Label(forecast_temp_frame, text=" - ", font=data_font, fg='white', bg='#2a2a2a')
                forecast_dash_label.pack(side='left')
                
                forecast_high_label = tk.Label(forecast_temp_frame, text="", font=data_font, fg='red', bg='#2a2a2a')
                forecast_high_label.pack(side='left')
                
                # WBGT予測値表フレーム
                wbgt_frame = tk.LabelFrame(location_frame, text="📊 WBGT予測値", 
                                         font=data_font, fg='#00ccff', bg='#2a2a2a')
                wbgt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                # 予測値表の作成
                table_frame = tk.Frame(wbgt_frame, bg='#2a2a2a')
                table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                # Treeviewで表を作成（各拠点用の小さな表）
                columns = ('time', 'value', 'level')
                # 縦幅をフォントサイズに応じて調整
                table_height = max(4, int(4 * config.FONT_SIZE_SMALL / 14.0))
                location_forecast_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=table_height)
                
                # カラムヘッダーの設定
                location_forecast_table.heading('time', text='時間')
                location_forecast_table.heading('value', text='WBGT')
                location_forecast_table.heading('level', text='警戒レベル')
                
                # カラム幅の設定（フォントサイズに応じて調整）
                col_width_multiplier = max(1.0, config.FONT_SIZE_SMALL / 14.0)
                location_forecast_table.column('time', width=int(60 * col_width_multiplier), anchor='center')
                location_forecast_table.column('value', width=int(60 * col_width_multiplier), anchor='center')
                location_forecast_table.column('level', width=int(80 * col_width_multiplier), anchor='center')
                
                # 表のスタイル設定
                style = ttk.Style()
                style.theme_use('clam')
                # 行の高さもフォントサイズに応じて調整
                row_height = max(20, int(20 * config.FONT_SIZE_SMALL / 14.0))
                style.configure('Treeview', background='#2a2a2a', foreground='white', 
                              fieldbackground='#2a2a2a', borderwidth=1,
                              font=('Helvetica', config.FONT_SIZE_SMALL),
                              rowheight=row_height)
                style.configure('Treeview.Heading', background='#404040', foreground='white',
                              borderwidth=1, font=('Helvetica', config.FONT_SIZE_SMALL, 'bold'))
                style.map('Treeview', background=[('selected', '#505050')])
                
                location_forecast_table.pack(fill=tk.BOTH, expand=True)
                
                # アラート情報フレーム
                alert_frame = tk.LabelFrame(location_frame, text="🚨 熱中症警戒アラート", 
                                          font=data_font, fg='#00ccff', bg='#2a2a2a')
                alert_frame.pack(fill=tk.X, padx=10, pady=5)
                
                today_alert_label = tk.Label(alert_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                today_alert_label.pack(anchor='w')
                
                tomorrow_alert_label = tk.Label(alert_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                tomorrow_alert_label.pack(anchor='w')
                
                # 週間予報フレーム（テーブル版）
                weekly_frame = tk.LabelFrame(location_frame, text="📅 週間天気予報", 
                                           font=data_font, fg='#00ccff', bg='#2a2a2a')
                weekly_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # 週間予報表の作成
                weekly_table_frame = tk.Frame(weekly_frame, bg='#2a2a2a')
                weekly_table_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Treeviewで週間予報表を作成
                weekly_columns = ('date', 'weather', 'pop', 'temp')
                weekly_forecast_table = ttk.Treeview(weekly_table_frame, columns=weekly_columns, show='headings', height=4)
                
                # カラムヘッダーの設定
                weekly_forecast_table.heading('date', text='日付')
                weekly_forecast_table.heading('weather', text='天気')
                weekly_forecast_table.heading('pop', text='降水確率')
                weekly_forecast_table.heading('temp', text='気温')
                
                # カラム幅の設定
                weekly_forecast_table.column('date', width=80, anchor='center')
                weekly_forecast_table.column('weather', width=80, anchor='center')
                weekly_forecast_table.column('pop', width=60, anchor='center')
                weekly_forecast_table.column('temp', width=80, anchor='center')
                
                weekly_forecast_table.pack(fill=tk.X)
                
                location_frames.append({
                    'forecast_low': forecast_low_label,
                    'forecast_high': forecast_high_label,
                    'weather_icon': weather_icon_label,
                    'weather_desc': weather_desc_label,
                    'forecast_table': location_forecast_table,
                    'weekly_forecast_table': weekly_forecast_table,
                    'today_alert': today_alert_label,
                    'tomorrow_alert': tomorrow_alert_label
                })
            
            # フッター
            footer_frame = tk.Frame(main_frame, bg='#1a1a1a')
            footer_frame.pack(fill=tk.X, pady=(20, 0))
            
            update_time_label = tk.Label(footer_frame, text="", font=data_font, fg='#888888', bg='#1a1a1a')
            update_time_label.pack()
            
            status_label = tk.Label(footer_frame, text="ESC キーで終了", font=data_font, fg='#888888', bg='#1a1a1a')
            status_label.pack()
            
            def get_wbgt_color(level):
                """WBGT警戒レベルに応じた色を返す"""
                colors = {
                    'ほぼ安全': '#0080ff',
                    '注意': '#00ff00',
                    '警戒': '#ffff00',
                    '厳重警戒': '#ff8000',
                    '危険': '#ff0000',
                    '極めて危険': '#800000'
                }
                return colors.get(level, '#ffffff')
            
            def get_alert_color(level):
                """アラートレベルに応じた色を返す"""
                if level >= 4:
                    return '#ff0000'
                elif level >= 3:
                    return '#ff8000'
                elif level >= 2:
                    return '#ffff00'
                else:
                    return '#888888'
            

            def update_gui():
                """GUI表示を更新"""
                try:
                    # 時刻更新
                    current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                    time_label.config(text=f"現在時刻: {current_time}")
                    
                    location_names = [loc['name'] for loc in self.locations]
                    locations_label.config(text=f"監視拠点: {' / '.join(location_names)}")
                    
                    # データ更新
                    if self.update_data():
                        # 各拠点のデータを表示
                        for i, location_data in enumerate(self.locations_data):
                            if i < len(location_frames):
                                frames = location_frames[i]
                                weather_data = location_data.get('weather_data')
                                alert_data = location_data.get('alert_data')
                                
                                if weather_data:
                                    # 天気情報
                                    frames['forecast_low'].config(text=f"{weather_data.get('forecast_low', 'N/A')}°C")
                                    frames['forecast_high'].config(text=f"{weather_data.get('forecast_high', 'N/A')}°C")
                                    
                                    # 天気アイコンと説明
                                    weather_code = weather_data.get('weather_code', '100')
                                    weather_api = self.weather_apis[0]  # 最初のAPIインスタンスを使用
                                    weather_emoji = weather_api.get_weather_emoji(weather_code)
                                    frames['weather_icon'].config(text=weather_emoji)
                                    frames['weather_desc'].config(text=f"天気: {weather_data.get('weather_description', 'Unknown')}")
                                    
                                    # WBGT予測値表を更新
                                    forecast_table = frames['forecast_table']
                                    
                                    # 既存の行をクリア
                                    for item in forecast_table.get_children():
                                        forecast_table.delete(item)
                                    
                                    # 現在値を追加
                                    current_data = location_data.get('env_wbgt_current')
                                    if current_data:
                                        level, _, _ = self.env_wbgt_api.get_wbgt_level_info(current_data['wbgt_value'])
                                        color = get_wbgt_color(level)
                                        item = forecast_table.insert('', 'end', values=('現在', f"{current_data.get('wbgt_value', 0):.1f}°C", level))
                                        forecast_table.set(item, 'level', level)
                                        # 行に色を適用
                                        forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
                                        forecast_table.item(item, tags=(f'level_{level}',))
                                    
                                    # 時系列予測値を追加
                                    timeseries_data = location_data.get('env_wbgt_timeseries')
                                    if timeseries_data and 'timeseries' in timeseries_data:
                                        timeseries = timeseries_data['timeseries']
                                        # 最初の3つの予測値を表示
                                        for j, data_point in enumerate(timeseries[:3]):
                                            level, _, _ = self.env_wbgt_api.get_wbgt_level_info(data_point['wbgt_value'])
                                            time_str = data_point['datetime_str']
                                            value_str = f"{data_point.get('wbgt_value', 0):.1f}°C"
                                            color = get_wbgt_color(level)
                                            item = forecast_table.insert('', 'end', values=(time_str, value_str, level))
                                            # 行に色を適用
                                            forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
                                            forecast_table.item(item, tags=(f'level_{level}',))
                                    
                                    # 週間予報表を更新
                                    weekly_forecast_table = frames['weekly_forecast_table']
                                    
                                    # 既存の行をクリア
                                    for item in weekly_forecast_table.get_children():
                                        weekly_forecast_table.delete(item)
                                    
                                    # 週間予報データを表に追加
                                    if 'weekly_forecast' in weather_data and weather_data['weekly_forecast']:
                                        for day in weather_data['weekly_forecast'][:7]:  # 最大7日間
                                            date_str = f"{day.get('date', 'Unknown')}({day.get('weekday', '')})"
                                            
                                            # 天気アイコンを取得
                                            day_weather_code = day.get('weather_code', '100')
                                            day_weather_emoji = weather_api.get_weather_emoji(day_weather_code)
                                            weather_desc = f"{day_weather_emoji}"  # アイコンのみ
                                            
                                            # 降水確率の処理
                                            if day['pop'] is not None and day['pop'] != '':
                                                pop = f"{day.get('pop', 0)}%"
                                            else:
                                                pop = '予報なし'
                                            
                                            # 気温の処理
                                            if day['temp_max'] is not None and day['temp_max'] != '':
                                                temp_max = day['temp_max']
                                            else:
                                                temp_max = '予報なし'
                                            
                                            if day['temp_min'] is not None and day['temp_min'] != '':
                                                temp_min = day['temp_min']
                                            else:
                                                temp_min = '予報なし'
                                            
                                            # 気温表示の処理
                                            if temp_max != '予報なし' or temp_min != '予報なし':
                                                if temp_max != '予報なし' and temp_min != '予報なし':
                                                    temp_range = f"{temp_max}/{temp_min}°C"
                                                elif temp_max != '予報なし':
                                                    temp_range = f"{temp_max}/--°C"
                                                else:
                                                    temp_range = f"--/{temp_min}°C"
                                            else:
                                                temp_range = '予報なし'
                                            
                                            # 降水確率に応じた色を決定
                                            pop_color = 'white'
                                            if pop != '予報なし':
                                                try:
                                                    pop_val = int(day['pop'])
                                                    if pop_val >= 70:
                                                        pop_color = '#ff6666'
                                                    elif pop_val >= 50:
                                                        pop_color = '#ffaa66'
                                                    elif pop_val >= 30:
                                                        pop_color = '#ffff66'
                                                except:
                                                    pass
                                            
                                            # 行を追加
                                            item_id = weekly_forecast_table.insert('', 'end', 
                                                values=(date_str, weather_desc, pop, temp_range))
                                            
                                            # 降水確率の色を設定
                                            weekly_forecast_table.tag_configure(f'pop_{pop_color}', 
                                                background='#2a2a2a', foreground=pop_color)
                                            weekly_forecast_table.item(item_id, tags=(f'pop_{pop_color}',))
                                    else:
                                        # データがない場合
                                        weekly_forecast_table.insert('', 'end', 
                                            values=('--', 'データなし', '--', '--'))
                                
                                if alert_data and 'alerts' in alert_data:
                                    # アラート情報
                                    today_alert = alert_data['alerts']['today']
                                    tomorrow_alert = alert_data['alerts']['tomorrow']
                                    
                                    today_color = get_alert_color(today_alert['level'])
                                    tomorrow_color = get_alert_color(tomorrow_alert['level'])
                                    
                                    frames['today_alert'].config(text=f"今日: {today_alert.get('status', 'Unknown')}", fg=today_color)
                                    frames['tomorrow_alert'].config(text=f"明日: {tomorrow_alert.get('status', 'Unknown')}", fg=tomorrow_color)
                        
                        # 更新時刻表示
                        if self.locations_data and self.locations_data[0].get('weather_data'):
                            update_time = self.locations_data[0]['weather_data']['timestamp']
                            update_time_label.config(text=f"最終更新: {update_time}")
                    
                    else:
                        status_label.config(text="データ取得エラー - ESC キーで終了", fg='#ff0000')
                
                except Exception as e:
                    self.logger.error(f"GUI更新エラー: {e}")
                    status_label.config(text=f"表示エラー: {e} - ESC キーで終了", fg='#ff0000')
                
                # 次回更新をスケジュール
                root.after(config.UPDATE_INTERVAL_MINUTES * 60 * 1000, update_gui)
            
            # 初回更新
            update_gui()
            
            # メインループ開始
            self.logger.info("GUI版キオスクアプリケーション開始")
            root.mainloop()
            
        except ImportError as e:
            print(f"❌ 必要なライブラリが利用できません: {e}")
            print("ターミナル版を起動します。")
            self.run_terminal_mode()
        except tk.TclError as e:
            print(f"❌ GUI表示エラー: {e}")
            print("ディスプレイ環境を確認してください。ターミナル版を起動します。")
            self.run_terminal_mode()
        except Exception as e:
            print(f"❌ GUI版でエラーが発生しました: {e}")
            print("ターミナル版を起動します。")
            self.run_terminal_mode()
        finally:
            self.logger.info("GUI版キオスクアプリケーション終了")
    
    def run(self):
        """メイン実行"""
        try:
            if self.demo_mode:
                self.run_demo_mode()
            elif self.gui_mode:
                self.run_gui_mode()
            else:
                self.run_terminal_mode()
        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            print(f"❌ エラー: {e}")
            sys.exit(1)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="WBGT熱中症警戒キオスク",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 wbgt_kiosk.py           # ターミナル版で起動
  python3 wbgt_kiosk.py --demo    # デモモードで起動
  python3 wbgt_kiosk.py --gui     # GUI版で起動（実験的）
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                        help='デモモードで起動（3回更新して終了）')
    parser.add_argument('--gui', action='store_true',
                        help='GUI版で起動（実験的）')
    
    args = parser.parse_args()
    
    try:
        kiosk = WBGTKiosk(demo_mode=args.demo, gui_mode=args.gui)
        kiosk.run()
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()