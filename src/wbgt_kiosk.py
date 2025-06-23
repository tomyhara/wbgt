#!/usr/bin/env python3
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
import time
import signal
import sys
import argparse
from datetime import datetime
import threading
import logging

# 設定の読み込み
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
    import config
except ImportError:
    print("❌ 設定ファイル setup/config.py が見つかりません。")
    print("📝 setup/config.sample.py をコピーして setup/config.py を作成してください。")
    sys.exit(1)

# GUI設定のデフォルト値を追加
if not hasattr(config, 'DISPLAY_WIDTH'):
    config.DISPLAY_WIDTH = 1024
if not hasattr(config, 'DISPLAY_HEIGHT'):
    config.DISPLAY_HEIGHT = 768
if not hasattr(config, 'FONT_SIZE_LARGE'):
    config.FONT_SIZE_LARGE = 20
if not hasattr(config, 'FONT_SIZE_MEDIUM'):
    config.FONT_SIZE_MEDIUM = 16
if not hasattr(config, 'FONT_SIZE_SMALL'):
    config.FONT_SIZE_SMALL = 12
if not hasattr(config, 'FULLSCREEN'):
    config.FULLSCREEN = False

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
        """ANSI色コードを取得"""
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
                    # まず実況値を試す
                    location_data['env_wbgt_data'] = self.env_wbgt_api.get_wbgt_current_data(location)
                    
                    # 実況値が取得できない場合は予測値を試す
                    if not location_data['env_wbgt_data']:
                        location_data['env_wbgt_data'] = self.env_wbgt_api.get_wbgt_forecast_data(location)
                    
                    if location_data['env_wbgt_data']:
                        # 環境省の公式データがある場合は優先使用
                        self._integrate_env_wbgt_data(location_data)
                        if not self.demo_mode:
                            data_type = location_data['env_wbgt_data'].get('data_type', 'unknown')
                            print(self.colored_text(f"✅ {location['name']} 環境省公式WBGTデータ取得完了 ({data_type})", 'green'))
                
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
        
        print(self.colored_text(f"🌤️  {location_name} - 現在の天気情報", 'cyan'))
        print("-" * 50)
        
        temp_text = f"{weather_data['temperature']}°C"
        humidity_text = f"{weather_data['humidity']}%"
        feels_like_text = f"{weather_data['feels_like']}°C"
        
        print(f"気温:     {self.colored_text(temp_text, 'yellow')}")
        print(f"湿度:     {self.colored_text(humidity_text, 'blue')}")
        print(f"天気:     {self.colored_text(weather_data['weather_description'], 'green')}")
        print(f"体感温度: {self.colored_text(feels_like_text, 'yellow')}")
        print()
    
    def display_wbgt(self, location_data):
        """WBGT情報を表示"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data:
            return
        
        wbgt_color = weather_data['wbgt_color']
        
        print(self.colored_text(f"🌡️  {location_name} - WBGT指数（熱中症指数）", 'cyan'))
        print("-" * 50)
        
        wbgt_text = f"{weather_data['wbgt']}°C"
        level_text = f"({weather_data['wbgt_level']})"
        
        print(f"WBGT指数: {self.colored_text(wbgt_text, wbgt_color)} " + 
              self.colored_text(level_text, wbgt_color))
        
        # データソース表示
        if 'wbgt_source' in weather_data:
            source_color = 'green' if '環境省' in weather_data['wbgt_source'] else 'yellow'
            print(f"データソース: {self.colored_text(weather_data['wbgt_source'], source_color)}")
        else:
            print(f"データソース: {self.colored_text('気象庁API（計算値）', 'yellow')}")
        
        print()
        print(f"📋 アドバイス:")
        print(f"   {self.colored_text(weather_data['wbgt_advice'], 'white')}")
        print()
        
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
        
        print(f"今日:   {self.colored_text(today_alert['status'], today_color)}")
        if today_alert['message']:
            print(f"        {today_alert['message']}")
        
        print(f"明日:   {self.colored_text(tomorrow_alert['status'], tomorrow_color)}")
        if tomorrow_alert['message']:
            print(f"        {tomorrow_alert['message']}")
        print()
    
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
            
            print("🪟 WBGT熱中症警戒キオスク GUI版を起動中...")
            
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
            
            location_frames = []
            for i, location in enumerate(self.locations):
                col = i % 2
                location_frame = tk.Frame(locations_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
                location_frame.grid(row=0, column=col, sticky='nsew', padx=10, pady=10)
                locations_frame.grid_columnconfigure(col, weight=1)
                locations_frame.grid_rowconfigure(0, weight=1)
                
                # 拠点名
                location_title = tk.Label(location_frame, 
                                        text=f"📍 {location['name']}",
                                        font=title_font, fg='#00ccff', bg='#2a2a2a')
                location_title.pack(pady=10)
                
                # 天気情報フレーム
                weather_frame = tk.LabelFrame(location_frame, text="🌤️ 天気情報", 
                                            font=data_font, fg='#00ccff', bg='#2a2a2a')
                weather_frame.pack(fill=tk.X, padx=10, pady=5)
                
                temp_label = tk.Label(weather_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                temp_label.pack(anchor='w')
                
                humidity_label = tk.Label(weather_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                humidity_label.pack(anchor='w')
                
                weather_label = tk.Label(weather_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                weather_label.pack(anchor='w')
                
                # WBGT情報フレーム
                wbgt_frame = tk.LabelFrame(location_frame, text="🌡️ WBGT指数", 
                                         font=data_font, fg='#00ccff', bg='#2a2a2a')
                wbgt_frame.pack(fill=tk.X, padx=10, pady=5)
                
                wbgt_value_label = tk.Label(wbgt_frame, text="", font=title_font, fg='white', bg='#2a2a2a')
                wbgt_value_label.pack()
                
                wbgt_level_label = tk.Label(wbgt_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                wbgt_level_label.pack()
                
                wbgt_advice_label = tk.Label(wbgt_frame, text="", font=data_font, fg='white', bg='#2a2a2a', wraplength=250)
                wbgt_advice_label.pack()
                
                wbgt_source_label = tk.Label(wbgt_frame, text="", font=('Helvetica', 10), fg='#888888', bg='#2a2a2a')
                wbgt_source_label.pack()
                
                # アラート情報フレーム
                alert_frame = tk.LabelFrame(location_frame, text="🚨 熱中症警戒アラート", 
                                          font=data_font, fg='#00ccff', bg='#2a2a2a')
                alert_frame.pack(fill=tk.X, padx=10, pady=5)
                
                today_alert_label = tk.Label(alert_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                today_alert_label.pack(anchor='w')
                
                tomorrow_alert_label = tk.Label(alert_frame, text="", font=data_font, fg='white', bg='#2a2a2a')
                tomorrow_alert_label.pack(anchor='w')
                
                location_frames.append({
                    'temp': temp_label,
                    'humidity': humidity_label,
                    'weather': weather_label,
                    'wbgt_value': wbgt_value_label,
                    'wbgt_level': wbgt_level_label,
                    'wbgt_advice': wbgt_advice_label,
                    'wbgt_source': wbgt_source_label,
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
                                    frames['temp'].config(text=f"気温: {weather_data['temperature']}°C")
                                    frames['humidity'].config(text=f"湿度: {weather_data['humidity']}%")
                                    frames['weather'].config(text=f"天気: {weather_data['weather_description']}")
                                    
                                    # WBGT情報
                                    wbgt_color = get_wbgt_color(weather_data['wbgt_level'])
                                    frames['wbgt_value'].config(text=f"{weather_data['wbgt']}°C", fg=wbgt_color)
                                    frames['wbgt_level'].config(text=f"({weather_data['wbgt_level']})", fg=wbgt_color)
                                    frames['wbgt_advice'].config(text=weather_data['wbgt_advice'])
                                    
                                    source_text = weather_data.get('wbgt_source', '気象庁API（計算値）')
                                    frames['wbgt_source'].config(text=f"データソース: {source_text}")
                                
                                if alert_data and 'alerts' in alert_data:
                                    # アラート情報
                                    today_alert = alert_data['alerts']['today']
                                    tomorrow_alert = alert_data['alerts']['tomorrow']
                                    
                                    today_color = get_alert_color(today_alert['level'])
                                    tomorrow_color = get_alert_color(tomorrow_alert['level'])
                                    
                                    frames['today_alert'].config(text=f"今日: {today_alert['status']}", fg=today_color)
                                    frames['tomorrow_alert'].config(text=f"明日: {tomorrow_alert['status']}", fg=tomorrow_color)
                        
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
            
        except ImportError:
            print("❌ tkinterが利用できません。ターミナル版を起動します。")
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