#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Components and Utilities for WBGT Kiosk
共通GUIコンポーネントとユーティリティ
"""

import tkinter as tk
from tkinter import ttk
import platform
import logging

logger = logging.getLogger(__name__)


class PlatformUtils:
    """プラットフォーム固有の処理を管理するクラス"""
    
    @staticmethod
    def is_windows():
        """Windows環境かどうかを判定"""
        return platform.system() == 'Windows'
    
    @staticmethod
    def is_macos():
        """macOS環境かどうかを判定"""
        return platform.system() == 'Darwin'
    
    @staticmethod
    def get_platform_message():
        """プラットフォーム固有の起動メッセージを取得"""
        system = platform.system()
        if system == 'Darwin':
            return "⚠️  macOS環境でのGUI起動を試行中..."
        elif system == 'Windows':
            return "⚠️  Windows環境での表示最適化を適用中..."
        else:
            return "⚠️  汎用環境で実行中..."


class ColorManager:
    """色管理を行うクラス"""
    
    @staticmethod
    def get_wbgt_color(level, is_windows=False):
        """WBGT警戒レベルに応じた色を返す"""
        if is_windows:
            # Windows環境では標準色名を使用
            colors = {
                'ほぼ安全': 'cyan', 'Safe': 'cyan',
                '注意': 'green', 'Caution': 'green',
                '警戒': 'yellow', 'Warning': 'yellow',
                '厳重警戒': 'orange', 'Severe Warning': 'orange',
                '危険': 'red', 'Dangerous': 'red',
                '極めて危険': 'darkred', 'Extremely Dangerous': 'darkred'
            }
        else:
            # その他の環境では16進数カラーコードを使用
            colors = {
                'ほぼ安全': '#0080ff', 'Safe': '#0080ff',
                '注意': '#00ff00', 'Caution': '#00ff00',
                '警戒': '#ffff00', 'Warning': '#ffff00',
                '厳重警戒': '#ff8000', 'Severe Warning': '#ff8000',
                '危険': '#ff0000', 'Dangerous': '#ff0000',
                '極めて危険': '#800000', 'Extremely Dangerous': '#800000'
            }
        return colors.get(level, 'white')
    
    @staticmethod
    def get_alert_color(level, is_windows=False):
        """アラートレベルに応じた色を返す"""
        if is_windows:
            if level >= 4:
                return 'red'
            elif level >= 3:
                return 'orange'
            elif level >= 2:
                return 'yellow'
            else:
                return 'gray'
        else:
            if level >= 4:
                return '#ff0000'
            elif level >= 3:
                return '#ff8000'
            elif level >= 2:
                return '#ffff00'
            else:
                return '#888888'


class WeatherIconManager:
    """天気アイコン管理クラス"""
    
    @staticmethod
    def get_precipitation_display(pop, pop_val, language='ja'):
        """降水確率に応じた表示文字列とアイコンを取得"""
        if language == 'ja':
            no_forecast = '予報なし'
            labels = ['(高)', '(中)', '(低)']
        else:
            no_forecast = 'No forecast'
            labels = ['(High)', '(Med)', '(Low)']
        
        if pop == no_forecast:
            return pop
        
        try:
            if pop_val >= 70:
                return f"🌧️ {pop} {labels[0]}"
            elif pop_val >= 50:
                return f"☔ {pop} {labels[1]}"
            elif pop_val >= 30:
                return f"🌦️ {pop} {labels[2]}"
            else:
                return f"☀️ {pop}"
        except (ValueError, TypeError):
            return pop


class TreeviewManager:
    """Treeview管理クラス"""
    
    @staticmethod
    def configure_style(font_size_small, is_windows=False):
        """Treeviewのスタイルを設定"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 行の高さを調整
        row_height = max(20, int(20 * font_size_small / 14.0))
        
        # 基本スタイル設定
        font_family = 'Arial' if is_windows else 'Helvetica'
        
        style.configure('Treeview', 
                       background='#2a2a2a', 
                       foreground='white',
                       fieldbackground='#2a2a2a', 
                       borderwidth=1,
                       font=(font_family, font_size_small),
                       rowheight=row_height)
        
        style.configure('Treeview.Heading', 
                       background='#404040', 
                       foreground='white',
                       borderwidth=1, 
                       font=(font_family, font_size_small, 'bold'))
        
        style.map('Treeview', background=[('selected', '#505050')])
        
        return style
    
    @staticmethod
    def setup_default_tags(treeview):
        """デフォルトタグを設定"""
        try:
            treeview.tag_configure('default', background='#2a2a2a', foreground='white')
        except Exception as e:
            logger.debug(f"デフォルトタグの設定に失敗: {e}")


class GUIComponentFactory:
    """GUI コンポーネント生成ファクトリークラス"""
    
    @staticmethod
    def create_location_frame(parent, location_name, config, is_windows=False):
        """拠点情報フレームを作成"""
        location_frame = tk.Frame(parent, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        
        # 拠点名
        location_title = tk.Label(location_frame, 
                                text=f"📍 {location_name}",
                                font=('Arial', config.FONT_SIZE_MEDIUM, 'bold'), 
                                fg='#00ccff', bg='#2a2a2a')
        location_title.pack(pady=10)
        
        return location_frame, location_title
    
    @staticmethod
    def create_weather_frame(parent, title, config, is_windows=False):
        """天気情報フレームを作成"""
        font_family = 'Arial' if is_windows else 'Helvetica'
        weather_frame = tk.LabelFrame(parent, text=title, 
                                    font=(font_family, config.FONT_SIZE_SMALL, 'bold'), 
                                    fg='#00ccff', bg='#2a2a2a')
        
        # 天気アイコンと説明を表示するフレーム
        weather_info_frame = tk.Frame(weather_frame, bg='#2a2a2a')
        weather_info_frame.pack(anchor='w', fill='x')
        
        weather_icon_label = tk.Label(weather_info_frame, text="", 
                                    font=('Arial', 20), fg='white', bg='#2a2a2a')
        weather_icon_label.pack(side='left')
        
        weather_desc_label = tk.Label(weather_info_frame, text="", 
                                    font=(font_family, config.FONT_SIZE_SMALL), 
                                    fg='white', bg='#2a2a2a')
        weather_desc_label.pack(side='left', padx=(5, 0))
        
        return weather_frame, weather_icon_label, weather_desc_label
    
    @staticmethod
    def create_forecast_temp_frame(parent, label_text, config, is_windows=False):
        """予想気温フレームを作成"""
        font_family = 'Arial' if is_windows else 'Helvetica'
        forecast_temp_frame = tk.Frame(parent, bg='#2a2a2a')
        forecast_temp_frame.pack(anchor='w', fill='x')
        
        forecast_label = tk.Label(forecast_temp_frame, text=label_text, 
                                font=(font_family, config.FONT_SIZE_SMALL), 
                                fg='white', bg='#2a2a2a')
        forecast_label.pack(side='left')
        
        forecast_low_label = tk.Label(forecast_temp_frame, text="", 
                                    font=(font_family, config.FONT_SIZE_SMALL), 
                                    fg='lightblue', bg='#2a2a2a')
        forecast_low_label.pack(side='left')
        
        forecast_dash_label = tk.Label(forecast_temp_frame, text=" - ", 
                                     font=(font_family, config.FONT_SIZE_SMALL), 
                                     fg='white', bg='#2a2a2a')
        forecast_dash_label.pack(side='left')
        
        forecast_high_label = tk.Label(forecast_temp_frame, text="", 
                                     font=(font_family, config.FONT_SIZE_SMALL), 
                                     fg='red', bg='#2a2a2a')
        forecast_high_label.pack(side='left')
        
        return forecast_temp_frame, forecast_low_label, forecast_high_label
    
    @staticmethod
    def create_wbgt_forecast_table(parent, config, is_windows=False):
        """WBGT予測値テーブルを作成"""
        table_frame = tk.Frame(parent, bg='#2a2a2a')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # テーブル作成
        columns = ('time', 'value', 'level')
        table_height = max(4, int(4 * config.FONT_SIZE_SMALL / 14.0))
        forecast_table = ttk.Treeview(table_frame, columns=columns, 
                                    show='headings', height=table_height)
        
        # カラム設定
        col_width_multiplier = max(1.0, config.FONT_SIZE_SMALL / 14.0)
        forecast_table.column('time', width=int(60 * col_width_multiplier), anchor='center')
        forecast_table.column('value', width=int(60 * col_width_multiplier), anchor='center')
        forecast_table.column('level', width=int(80 * col_width_multiplier), anchor='center')
        
        # スタイル適用
        TreeviewManager.configure_style(config.FONT_SIZE_SMALL, is_windows)
        TreeviewManager.setup_default_tags(forecast_table)
        
        forecast_table.pack(fill=tk.BOTH, expand=True)
        
        return forecast_table
    
    @staticmethod
    def create_weekly_forecast_table(parent, config, language='ja', is_windows=False):
        """週間予報テーブルを作成"""
        weekly_table_frame = tk.Frame(parent, bg='#2a2a2a')
        weekly_table_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # テーブル作成
        weekly_columns = ('date', 'weather', 'pop', 'temp')
        weekly_forecast_table = ttk.Treeview(weekly_table_frame, columns=weekly_columns, 
                                           show='headings', height=4)
        
        # ヘッダー設定（言語対応）
        if language == 'ja':
            headers = {'date': '日付', 'weather': '天気', 'pop': '降水確率', 'temp': '気温'}
        else:
            headers = {'date': 'Date', 'weather': 'Weather', 'pop': 'Rain %', 'temp': 'Temp'}
        
        for col, header in headers.items():
            weekly_forecast_table.heading(col, text=header)
        
        # カラム幅設定
        weekly_forecast_table.column('date', width=80, anchor='center')
        weekly_forecast_table.column('weather', width=80, anchor='center')
        weekly_forecast_table.column('pop', width=60, anchor='center')
        weekly_forecast_table.column('temp', width=80, anchor='center')
        
        # スタイル適用
        TreeviewManager.configure_style(config.FONT_SIZE_SMALL, is_windows)
        TreeviewManager.setup_default_tags(weekly_forecast_table)
        
        weekly_forecast_table.pack(fill=tk.X)
        
        return weekly_forecast_table


class WeatherDataProcessor:
    """天気データ処理クラス"""
    
    @staticmethod
    def process_weekly_forecast_data(weekly_forecast, weather_api, language='ja'):
        """週間予報データを処理"""
        if not weekly_forecast:
            return []
        
        processed_data = []
        no_forecast = '予報なし' if language == 'ja' else 'No forecast'
        
        for day in weekly_forecast[:7]:  # 最大7日間
            date_str = f"{day.get('date', 'Unknown')}({day.get('weekday', '')})"
            
            # 天気アイコン取得
            weather_code = day.get('weather_code', '100')
            weather_emoji = weather_api.get_weather_emoji(weather_code)
            
            # 降水確率処理
            pop = f"{day.get('pop', 0)}%" if day['pop'] is not None and day['pop'] != '' else no_forecast
            pop_val = day.get('pop', 0) if day['pop'] is not None and day['pop'] != '' else 0
            pop_display = WeatherIconManager.get_precipitation_display(pop, pop_val, language)
            
            # 気温処理
            temp_max = day['temp_max'] if day['temp_max'] is not None and day['temp_max'] != '' else no_forecast
            temp_min = day['temp_min'] if day['temp_min'] is not None and day['temp_min'] != '' else no_forecast
            
            if temp_max != no_forecast or temp_min != no_forecast:
                if temp_max != no_forecast and temp_min != no_forecast:
                    temp_range = f"{temp_max}/{temp_min}°C"
                elif temp_max != no_forecast:
                    temp_range = f"{temp_max}/--°C"
                else:
                    temp_range = f"--/{temp_min}°C"
            else:
                temp_range = no_forecast
            
            processed_data.append({
                'date': date_str,
                'weather': weather_emoji,
                'pop': pop_display,
                'temp': temp_range
            })
        
        return processed_data