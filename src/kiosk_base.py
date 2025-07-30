#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base class for WBGT Kiosk applications
WBGT キオスクアプリケーションのベースクラス
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from gui_components import PlatformUtils


class WBGTKioskBase:
    """WBGT キオスクの基底クラス"""
    
    def __init__(self, config, demo_mode=False, gui_mode=False):
        self.config = config
        self.demo_mode = demo_mode
        self.gui_mode = gui_mode
        self.demo_count = 0
        self.running = True
        self.locations = config.LOCATIONS
        self.locations_data = []
        
        # ログ設定
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """ログの設定"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL.upper(), logging.INFO),
            format=log_format,
            handlers=[
                logging.FileHandler(self.config.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def signal_handler(self, sig=None, frame=None):
        """シグナルハンドラー"""
        self.logger.info("終了シグナルを受信")
        self.running = False
        print("\n🛑 WBGTキオスクを終了中...")
        sys.exit(0)
    
    def clear_screen(self):
        """画面をクリア"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_color_code(self, color_name):
        """ANSI色コードを取得（Windows互換）"""
        if PlatformUtils.is_windows():
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
    
    def display_header(self):
        """ヘッダーを表示（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement display_header")
    
    def display_footer(self):
        """フッターを表示（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement display_footer")
    
    def update_data(self):
        """データを更新（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement update_data")
    
    def display_all(self):
        """全体表示（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement display_all")
    
    def run_demo_mode(self):
        """デモモード実行（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement run_demo_mode")
    
    def run_terminal_mode(self):
        """ターミナルモード実行"""
        self.logger.info("ターミナルキオスクアプリケーション開始")
        
        print(self.colored_text("WBGTキオスク起動中...", 'cyan'))
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
                interval_seconds = self.config.UPDATE_INTERVAL_MINUTES * 60
                for i in range(interval_seconds):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.clear_screen()
            print(self.colored_text("WBGTキオスクを終了しました", 'cyan'))
            self.logger.info("ターミナルキオスクアプリケーション終了")
    
    def run_gui_mode(self):
        """GUI モード実行（サブクラスでオーバーライド）"""
        raise NotImplementedError("Subclass must implement run_gui_mode")
    
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


class GUIUpdateMixin:
    """GUI更新に関する共通処理"""
    
    def update_wbgt_forecast_table(self, forecast_table, location_data, get_wbgt_color_func):
        """WBGT予測値表を更新"""
        # 既存の行をクリア
        for item in forecast_table.get_children():
            forecast_table.delete(item)
        
        # 現在値を追加
        current_data = location_data.get('env_wbgt_current')
        if current_data:
            level, _, _ = self.env_wbgt_api.get_wbgt_level_info(current_data['wbgt_value'])
            color = get_wbgt_color_func(level)
            item = forecast_table.insert('', 'end', 
                values=('現在' if hasattr(self, 'language') and self.language == 'ja' else 'Current', 
                       f"{current_data.get('wbgt_value', 0):.1f}°C", level))
            forecast_table.set(item, 'level', level)
            # 行に色を適用
            forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
            forecast_table.item(item, tags=(f'level_{level}',))
        
        # 時系列予測値を追加
        timeseries_data = location_data.get('env_wbgt_timeseries')
        if timeseries_data and 'timeseries' in timeseries_data:
            timeseries = timeseries_data['timeseries']
            # 最初の3つの予測値を表示
            for data_point in timeseries[:3]:
                level, _, _ = self.env_wbgt_api.get_wbgt_level_info(data_point['wbgt_value'])
                time_str = data_point['datetime_str']
                value_str = f"{data_point.get('wbgt_value', 0):.1f}°C"
                color = get_wbgt_color_func(level)
                item = forecast_table.insert('', 'end', values=(time_str, value_str, level))
                # 行に色を適用
                forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
                forecast_table.item(item, tags=(f'level_{level}',))