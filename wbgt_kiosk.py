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
    import config
except ImportError:
    print("❌ 設定ファイル config.py が見つかりません。")
    print("📝 config.sample.py をコピーして config.py を作成してください。")
    sys.exit(1)

from jma_api import JMAWeatherAPI
from heatstroke_alert import HeatstrokeAlert
from env_wbgt_api import EnvWBGTAPI

class WBGTKiosk:
    """WBGT熱中症警戒キオスクのメインクラス"""
    
    def __init__(self, demo_mode=False, gui_mode=False):
        self.demo_mode = demo_mode
        self.gui_mode = gui_mode
        self.weather_api = JMAWeatherAPI(area_code=config.AREA_CODE)
        self.heatstroke_alert = HeatstrokeAlert()
        self.env_wbgt_api = EnvWBGTAPI()
        self.weather_data = None
        self.alert_data = None
        self.env_wbgt_data = None
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
        """データを更新"""
        try:
            self.logger.info("データ更新開始")
            if not self.demo_mode:
                print("📡 データ取得中...")
            
            # 気象庁APIからデータ取得
            self.weather_data = self.weather_api.get_weather_data()
            self.alert_data = self.heatstroke_alert.get_alert_data()
            
            # 環境省WBGTサービスからデータ取得（サービス期間内の場合）
            if self.env_wbgt_api.is_service_available():
                # まず実況値を試す
                self.env_wbgt_data = self.env_wbgt_api.get_wbgt_current_data(config.CITY_NAME)
                
                # 実況値が取得できない場合は予測値を試す
                if not self.env_wbgt_data:
                    self.env_wbgt_data = self.env_wbgt_api.get_wbgt_forecast_data(config.CITY_NAME)
                
                if self.env_wbgt_data:
                    # 環境省の公式データがある場合は優先使用
                    self._integrate_env_wbgt_data()
                    if not self.demo_mode:
                        data_type = self.env_wbgt_data.get('data_type', 'unknown')
                        print(self.colored_text(f"✅ 環境省公式WBGTデータ取得完了 ({data_type})", 'green'))
            
            if not self.demo_mode:
                print(self.colored_text("✅ データ取得完了", 'green'))
            
            self.logger.info("データ更新完了")
            return True
            
        except Exception as e:
            self.logger.error(f"データ更新エラー: {e}")
            if not self.demo_mode:
                print(self.colored_text(f"❌ データ取得エラー: {e}", 'red'))
            return False
    
    def _integrate_env_wbgt_data(self):
        """環境省WBGTデータを気象庁データと統合"""
        if self.env_wbgt_data and self.weather_data:
            # 環境省の公式WBGT値を使用
            official_wbgt = self.env_wbgt_data['wbgt_value']
            level, color, advice = self.env_wbgt_api.get_wbgt_level_info(official_wbgt)
            
            # 既存の天気データを更新
            self.weather_data.update({
                'wbgt': official_wbgt,
                'wbgt_level': level,
                'wbgt_color': color,
                'wbgt_advice': advice,
                'wbgt_source': '環境省公式データ'
            })
            
            self.logger.info(f"環境省公式WBGT値を使用: {official_wbgt}°C")
    
    def display_header(self):
        """ヘッダーを表示"""
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        mode_text = "デモモード" if self.demo_mode else "運用モード"
        
        print("=" * 80)
        print(self.colored_text("           🌡️  WBGT熱中症警戒キオスク  🌡️", 'cyan'))
        print("=" * 80)
        print(f"現在時刻: {self.colored_text(current_time, 'white')}")
        print(f"地域: {self.colored_text(config.CITY_NAME, 'cyan')}")
        if self.demo_mode:
            print(f"モード: {self.colored_text(mode_text, 'yellow')} ({self.demo_count + 1}/3)")
        print("-" * 80)
    
    def display_weather(self):
        """天気情報を表示"""
        if not self.weather_data:
            print(self.colored_text("❌ 天気データを取得できませんでした", 'red'))
            return
        
        print(self.colored_text("🌤️  現在の天気情報", 'cyan'))
        print("-" * 40)
        
        temp_text = f"{self.weather_data['temperature']}°C"
        humidity_text = f"{self.weather_data['humidity']}%"
        feels_like_text = f"{self.weather_data['feels_like']}°C"
        
        print(f"気温:     {self.colored_text(temp_text, 'yellow')}")
        print(f"湿度:     {self.colored_text(humidity_text, 'blue')}")
        print(f"天気:     {self.colored_text(self.weather_data['weather_description'], 'green')}")
        print(f"体感温度: {self.colored_text(feels_like_text, 'yellow')}")
        print()
    
    def display_wbgt(self):
        """WBGT情報を表示"""
        if not self.weather_data:
            return
        
        wbgt_color = self.weather_data['wbgt_color']
        
        print(self.colored_text("🌡️  WBGT指数（熱中症指数）", 'cyan'))
        print("-" * 40)
        
        wbgt_text = f"{self.weather_data['wbgt']}°C"
        level_text = f"({self.weather_data['wbgt_level']})"
        
        print(f"WBGT指数: {self.colored_text(wbgt_text, wbgt_color)} " + 
              self.colored_text(level_text, wbgt_color))
        
        # データソース表示
        if 'wbgt_source' in self.weather_data:
            source_color = 'green' if '環境省' in self.weather_data['wbgt_source'] else 'yellow'
            print(f"データソース: {self.colored_text(self.weather_data['wbgt_source'], source_color)}")
        else:
            print(f"データソース: {self.colored_text('気象庁API（計算値）', 'yellow')}")
        
        print()
        print(f"📋 アドバイス:")
        print(f"   {self.colored_text(self.weather_data['wbgt_advice'], 'white')}")
        print()
        
        # WBGT レベル表示
        level = self.weather_data['wbgt_level']
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
    
    def display_alerts(self):
        """熱中症警戒アラートを表示"""
        if not self.alert_data:
            print(self.colored_text("❌ アラートデータを取得できませんでした", 'red'))
            return
        
        print(self.colored_text("🚨 熱中症警戒アラート", 'cyan'))
        print("-" * 40)
        
        today_alert = self.alert_data['alerts']['today']
        tomorrow_alert = self.alert_data['alerts']['tomorrow']
        
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
        if self.weather_data:
            update_time = self.weather_data['timestamp']
            print(f"最終更新: {self.colored_text(update_time, 'gray')}")
        
        if self.demo_mode:
            if self.demo_count < 2:
                print(self.colored_text("5秒後に再更新します...", 'gray'))
            else:
                print(self.colored_text("デモ完了！", 'green'))
        else:
            interval = config.UPDATE_INTERVAL_MINUTES
            print(self.colored_text(f"Ctrl+C で終了 | {interval}分ごとに自動更新", 'gray'))
        
        print("=" * 80)
    
    def display_all(self):
        """全体表示"""
        self.clear_screen()
        self.display_header()
        self.display_weather()
        self.display_wbgt()
        self.display_alerts()
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
        """GUI モード実行（実験的）"""
        try:
            import tkinter as tk
            print("🪟 GUI版は実験的機能です")
            print("⚠️ 表示に問題がある場合はターミナル版をご利用ください")
            
            # 簡単なGUI実装
            root = tk.Tk()
            root.title("WBGT熱中症警戒キオスク")
            root.geometry("600x400")
            
            text_widget = tk.Text(root, bg='black', fg='white', font=('monospace', 12))
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            def update_gui():
                if self.update_data():
                    # ターミナル出力をGUIに表示
                    text_widget.delete(1.0, tk.END)
                    text_widget.insert(tk.END, f"WBGT熱中症警戒キオスク\n")
                    text_widget.insert(tk.END, f"=" * 50 + "\n")
                    
                    if self.weather_data:
                        text_widget.insert(tk.END, f"気温: {self.weather_data['temperature']}°C\n")
                        text_widget.insert(tk.END, f"湿度: {self.weather_data['humidity']}%\n")
                        text_widget.insert(tk.END, f"天気: {self.weather_data['weather_description']}\n")
                        text_widget.insert(tk.END, f"WBGT: {self.weather_data['wbgt']}°C ({self.weather_data['wbgt_level']})\n")
                        text_widget.insert(tk.END, f"アドバイス: {self.weather_data['wbgt_advice']}\n")
                
                root.after(config.UPDATE_INTERVAL_MINUTES * 60 * 1000, update_gui)
            
            update_gui()
            root.mainloop()
            
        except ImportError:
            print("❌ tkinterが利用できません。ターミナル版を起動します。")
            self.run_terminal_mode()
        except Exception as e:
            print(f"❌ GUI版でエラーが発生しました: {e}")
            print("ターミナル版を起動します。")
            self.run_terminal_mode()
    
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