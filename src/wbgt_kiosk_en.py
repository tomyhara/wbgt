#!/usr/bin/env python3
"""
WBGT Heat Stroke Warning Kiosk (English Version)
Kiosk terminal displaying heat stroke warning alerts and weather for Raspberry Pi

Usage:
    python3 wbgt_kiosk_en.py [--demo] [--gui]
    
Options:
    --demo    Short demo mode (3 updates then exit)
    --gui     Launch in GUI mode (experimental)
    Default: Launch in terminal mode
"""
import os
import time
import signal
import sys
import argparse
from datetime import datetime
import threading
import logging

# Load configuration
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'setup'))
    import config_en
except ImportError:
    print("❌ Configuration file setup/config_en.py not found.")
    print("📝 Please copy setup/config_en.sample.py and create setup/config_en.py.")
    sys.exit(1)

# Add GUI configuration defaults
if not hasattr(config_en, 'DISPLAY_WIDTH'):
    config_en.DISPLAY_WIDTH = 1024
if not hasattr(config_en, 'DISPLAY_HEIGHT'):
    config_en.DISPLAY_HEIGHT = 768
if not hasattr(config_en, 'FONT_SIZE_LARGE'):
    config_en.FONT_SIZE_LARGE = 20
if not hasattr(config_en, 'FONT_SIZE_MEDIUM'):
    config_en.FONT_SIZE_MEDIUM = 16
if not hasattr(config_en, 'FONT_SIZE_SMALL'):
    config_en.FONT_SIZE_SMALL = 12
if not hasattr(config_en, 'FULLSCREEN'):
    config_en.FULLSCREEN = False

from jma_api_en import JMAWeatherAPIEN
from heatstroke_alert_en import HeatstrokeAlertEN
from env_wbgt_api_en import EnvWBGTAPIEN

class WBGTKioskEN:
    """Main class for WBGT Heat Stroke Warning Kiosk (English)"""
    
    def __init__(self, demo_mode=False, gui_mode=False):
        self.demo_mode = demo_mode
        self.gui_mode = gui_mode
        self.demo_count = 0
        self.running = True
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('wbgt_kiosk_en.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.locations = config_en.LOCATIONS
        self.update_interval = config_en.UPDATE_INTERVAL_MINUTES
        
        # Initialize APIs
        self.weather_apis = []
        for location in self.locations:
            area_code = location.get('area_code', '130000')  # Default to Tokyo
            self.weather_apis.append(JMAWeatherAPIEN(area_code))
        
        self.heatstroke_alert = HeatstrokeAlertEN()
        self.env_wbgt_api = EnvWBGTAPIEN()
        
        # Data storage
        self.locations_data = []
        
        # Signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.running = False
        print("\n🛑 Shutting down WBGT Kiosk...")
        sys.exit(0)
    
    def colored_text(self, text, color):
        """Return colored text for terminal display"""
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'orange': '\033[93m',
            'darkred': '\033[31m',
            'gray': '\033[90m',
            'reset': '\033[0m'
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def update_data(self):
        """Update weather and WBGT data"""
        try:
            self.logger.info("Starting data update")
            if not self.demo_mode:
                print("📡 Fetching data...")
            
            self.locations_data = []
            
            for i, location in enumerate(self.locations):
                location_data = {
                    'location': location,
                    'weather_data': None,
                    'alert_data': None,
                    'env_wbgt_data': None
                }
                
                # Get data from JMA API
                location_data['weather_data'] = self.weather_apis[i].get_weather_data()
                location_data['alert_data'] = self.heatstroke_alert.get_alert_data(location.get('prefecture', 'Tokyo'))
                
                # Get data from Environment Ministry WBGT service (if available)
                if self.env_wbgt_api.is_service_available():
                    # Get both current and forecast data
                    current_data = self.env_wbgt_api.get_wbgt_current_data(location)
                    forecast_data = self.env_wbgt_api.get_wbgt_forecast_data(location)
                    
                    # For GUI mode, also get timeseries data
                    if self.gui_mode:
                        forecast_timeseries = self.env_wbgt_api.get_wbgt_forecast_timeseries(location)
                        location_data['env_wbgt_timeseries'] = forecast_timeseries
                    
                    # Store both data types
                    location_data['env_wbgt_current'] = current_data
                    location_data['env_wbgt_forecast'] = forecast_data
                    
                    # Determine main data for display (prioritize current data)
                    if current_data:
                        location_data['env_wbgt_data'] = current_data
                    elif forecast_data:
                        location_data['env_wbgt_data'] = forecast_data
                    
                    if location_data['env_wbgt_data']:
                        # Use official Environment Ministry data when available
                        wbgt_value = location_data['env_wbgt_data']['wbgt_value']
                        level, color, advice = self.env_wbgt_api.get_wbgt_level_info(wbgt_value)
                        
                        # Update weather data with official WBGT
                        if location_data['weather_data']:
                            location_data['weather_data']['wbgt'] = wbgt_value
                            location_data['weather_data']['wbgt_level'] = level
                            location_data['weather_data']['wbgt_color'] = color
                            location_data['weather_data']['wbgt_advice'] = advice
                            location_data['weather_data']['wbgt_source'] = 'Official Environment Ministry Data'
                        
                        if not self.demo_mode:
                            data_types = []
                            if current_data:
                                data_types.append('Current')
                            if forecast_data:
                                data_types.append('Forecast')
                            print(self.colored_text(f"✅ {location['name']} Official Environment Ministry WBGT data acquired ({'/'.join(data_types)})", 'green'))
                        
                        self.logger.info(f"{location['name']} Using official Environment Ministry WBGT: {wbgt_value}°C")
                
                self.locations_data.append(location_data)
            
            self.logger.info("Data update completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Data update error: {e}")
            return False
    
    def display_header(self):
        """Display header information"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        location_names = " / ".join([loc['name'] for loc in self.locations])
        
        print("=" * 120)
        print(self.colored_text("           🌡️  WBGT Heat Stroke Warning Kiosk (Multi-Location)  🌡️", 'cyan'))
        print("=" * 120)
        print(f"Current Time: {self.colored_text(current_time, 'white')}")
        print(f"Monitoring Locations: {self.colored_text(location_names, 'cyan')}")
        
        if self.demo_mode:
            mode_text = "Demo Mode"
            print(f"Mode: {self.colored_text(mode_text, 'yellow')} ({self.demo_count + 1}/3)")
        print("-" * 120)
    
    def display_weather(self, location_data):
        """Display weather information"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data:
            print(self.colored_text(f"❌ {location_name} Unable to fetch weather data", 'red'))
            return
        
        print(self.colored_text(f"🌤️  {location_name} - Current Weather Information", 'cyan'))
        print("-" * 50)
        
        temp_text = f"{weather_data['temperature']}°C"
        humidity_text = f"{weather_data['humidity']}%"
        feels_like_text = f"{weather_data['feels_like']}°C"
        
        print(f"Temperature:  {self.colored_text(temp_text, 'yellow')}")
        print(f"Humidity:     {self.colored_text(humidity_text, 'blue')}")
        print(f"Weather:      {self.colored_text(weather_data['weather_description'], 'green')}")
        print(f"Feels Like:   {self.colored_text(feels_like_text, 'yellow')}")
        print()
    
    def display_wbgt(self, location_data):
        """Display WBGT information"""
        weather_data = location_data['weather_data']
        location_name = location_data['location']['name']
        
        if not weather_data:
            return
        
        wbgt_color = weather_data['wbgt_color']
        
        print(self.colored_text(f"🌡️  {location_name} - WBGT Index (Heat Stroke Index)", 'cyan'))
        print("-" * 50)
        
        wbgt_text = f"{weather_data['wbgt']}°C"
        level_text = f"({weather_data['wbgt_level']})"
        
        print(f"WBGT Index: {self.colored_text(wbgt_text, wbgt_color)} " + 
              self.colored_text(level_text, wbgt_color))
        
        # Display Environment Ministry data for both current and forecast
        current_data = location_data.get('env_wbgt_current')
        forecast_data = location_data.get('env_wbgt_forecast')
        
        if current_data or forecast_data:
            print()
            print(f"📊 Official Environment Ministry Data:")
            if current_data:
                current_level, current_color, _ = self.env_wbgt_api.get_wbgt_level_info(current_data['wbgt_value'])
                print(f"   Current: {self.colored_text(f'{current_data['wbgt_value']}°C', current_color)} " +
                      f"({self.colored_text(current_level, current_color)})")
                if 'datetime' in current_data:
                    print(f"   Update Time: {current_data['datetime']}")
            if forecast_data:
                forecast_level, forecast_color, _ = self.env_wbgt_api.get_wbgt_level_info(forecast_data['wbgt_value'])
                print(f"   Forecast: {self.colored_text(f'{forecast_data['wbgt_value']}°C', forecast_color)} " +
                      f"({self.colored_text(forecast_level, forecast_color)})")
                if 'update_time' in forecast_data:
                    print(f"   Update Time: {forecast_data['update_time']}")
        
        # Display data source
        if 'wbgt_source' in weather_data:
            source_color = 'green' if 'Environment Ministry' in weather_data['wbgt_source'] else 'yellow'
            print(f"Data Source: {self.colored_text(weather_data['wbgt_source'], source_color)}")
        else:
            print(f"Data Source: {self.colored_text('JMA API (Calculated)', 'yellow')}")
        
        print()
        print(f"📋 Advice:")
        print(f"   {self.colored_text(weather_data['wbgt_advice'], 'white')}")
        print()
        
        # WBGT level display
        level = weather_data['wbgt_level']
        if level == "Extremely Dangerous" or level == "Dangerous":
            indicator = "🚨🚨🚨 DANGEROUS 🚨🚨🚨"
        elif level == "Severe Warning":
            indicator = "⚠️⚠️ SEVERE WARNING ⚠️⚠️"
        elif level == "Warning":
            indicator = "⚠️ WARNING ⚠️"
        elif level == "Caution":
            indicator = "⚠️ CAUTION"
        else:
            indicator = "✅ SAFE"
        
        print(f"Level: {self.colored_text(indicator, wbgt_color)}")
        print()
    
    def display_alerts(self, location_data):
        """Display heat stroke warning alerts"""
        alert_data = location_data['alert_data']
        location_name = location_data['location']['name']
        
        if not alert_data:
            print(self.colored_text(f"❌ {location_name} Unable to fetch alert data", 'red'))
            return
        
        print(self.colored_text(f"🚨 {location_name} - Heat Stroke Warning Alert", 'cyan'))
        print("-" * 50)
        
        today_alert = alert_data['alerts']['today']
        tomorrow_alert = alert_data['alerts']['tomorrow']
        
        today_color = self.heatstroke_alert.get_alert_color(today_alert['level'])
        tomorrow_color = self.heatstroke_alert.get_alert_color(tomorrow_alert['level'])
        
        print(f"Today:    {self.colored_text(today_alert['status'], today_color)}")
        if today_alert['message']:
            print(f"          {today_alert['message']}")
        
        print(f"Tomorrow: {self.colored_text(tomorrow_alert['status'], tomorrow_color)}")
        if tomorrow_alert['message']:
            print(f"          {tomorrow_alert['message']}")
        print()
    
    def display_footer(self):
        """Display footer information"""
        if self.locations_data and self.locations_data[0].get('weather_data'):
            last_updated = self.locations_data[0]['weather_data']['timestamp']
            print(f"Last Updated: {self.colored_text(last_updated, 'gray')}")
        
        if not self.demo_mode:
            print(self.colored_text(f"Next update in {self.update_interval} minutes...", 'gray'))
        print("=" * 120)
    
    def run_demo_mode(self):
        """Run in demo mode"""
        print(self.colored_text("🚀 WBGT Heat Stroke Warning Kiosk Demo Mode", 'cyan'))
        print()
        print("📝 This demo automatically checks:")
        print("  ✅ Weather data retrieval from JMA API")
        print("  ✅ WBGT index calculation and display")
        print("  ✅ Heat stroke warning level determination")
        print("  ✅ Colored terminal display")
        print()
        print("⏱️ Will update 3 times then exit")
        print()
        
        for i in range(3, 0, -1):
            print(f"Demo starts in {i} seconds...")
            time.sleep(1)
        print()
        
        for demo_round in range(3):
            if not self.running:
                break
                
            self.demo_count = demo_round
            print(f"=== Demo {demo_round + 1}/3 ===")
            
            if self.update_data():
                self.clear_screen()
                self.display_header()
                
                for location_data in self.locations_data:
                    self.display_weather(location_data)
                    self.display_wbgt(location_data)
                    self.display_alerts(location_data)
                    print("=" * 120)
                    print()
                
                self.display_footer()
                
                if demo_round < 2:
                    for countdown in range(5, 0, -1):
                        print(f"Next update in {countdown} seconds...", end="   ")
                        time.sleep(1)
                    print()
            else:
                print("❌ Failed to fetch data")
            
            print()
        
        print("=" * 80)
        print(self.colored_text("🎉 Demo completed! WBGT Kiosk is working properly.", 'green'))
        print()
        print("📱 For production use, run:")
        print(f"   {self.colored_text('./run_wbgt.sh', 'cyan')}")
        print("=" * 80)
    
    def run_terminal_mode(self):
        """Run in terminal mode"""
        print(self.colored_text("🚀 WBGT Heat Stroke Warning Kiosk Terminal Mode", 'cyan'))
        print("Press Ctrl+C to exit")
        print()
        
        while self.running:
            try:
                if self.update_data():
                    self.clear_screen()
                    self.display_header()
                    
                    for location_data in self.locations_data:
                        self.display_weather(location_data)
                        self.display_wbgt(location_data)
                        self.display_alerts(location_data)
                        print("=" * 120)
                        print()
                    
                    self.display_footer()
                else:
                    print("❌ Failed to fetch data. Retrying in 1 minute...")
                
                # Wait for next update
                for remaining in range(self.update_interval * 60, 0, -1):
                    if not self.running:
                        break
                    time.sleep(1)
                
            except KeyboardInterrupt:
                break
        
        self.logger.info("Terminal mode kiosk application ended")
    
    def run_gui_mode(self):
        """Run in GUI mode"""
        try:
            import tkinter as tk
            from tkinter import ttk
            
            # Create main window
            root = tk.Tk()
            root.title("WBGT Heat Stroke Warning Kiosk")
            root.geometry(f"{config_en.DISPLAY_WIDTH}x{config_en.DISPLAY_HEIGHT}")
            root.configure(bg='black')
            
            if config_en.FULLSCREEN:
                root.attributes('-fullscreen', True)
            
            # Exit handler
            def on_escape(event):
                self.running = False
                root.quit()
                root.destroy()
            
            root.bind('<Escape>', on_escape)
            root.focus_set()
            
            # Create main frame
            main_frame = tk.Frame(root, bg='black')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)
            
            # Title
            title_label = tk.Label(
                main_frame,
                text="🌡️ WBGT Heat Stroke Warning Kiosk 🌡️",
                font=('Arial', config_en.FONT_SIZE_LARGE, 'bold'),
                fg='cyan',
                bg='black'
            )
            title_label.pack(pady=(0, 20))
            
            # Status label
            status_label = tk.Label(
                main_frame,
                text="Starting up...",
                font=('Arial', config_en.FONT_SIZE_MEDIUM),
                fg='white',
                bg='black'
            )
            status_label.pack(pady=(0, 10))
            
            # Locations container frame
            locations_frame = tk.Frame(main_frame, bg='black')
            locations_frame.pack(fill='both', expand=True, pady=10)
            
            # Location frames (2-column layout)
            location_frames = []
            for i, location in enumerate(self.locations):
                col = i % 2
                location_frame = tk.Frame(locations_frame, bg='#2a2a2a', relief=tk.RAISED, bd=2)
                location_frame.grid(row=0, column=col, sticky='nsew', padx=10, pady=10)
                locations_frame.grid_columnconfigure(col, weight=1, uniform='location')
                locations_frame.grid_rowconfigure(0, weight=1)
                
                # Location title
                location_title = tk.Label(location_frame, 
                                        text=f"📍 {location['name']}",
                                        font=('Arial', config_en.FONT_SIZE_MEDIUM, 'bold'), 
                                        fg='#00ccff', bg='#2a2a2a')
                location_title.pack(pady=10)
                
                # Weather info frame
                weather_frame = tk.LabelFrame(location_frame, text="🌤️ Weather Info", 
                                            font=('Arial', config_en.FONT_SIZE_SMALL, 'bold'), fg='#00ccff', bg='#2a2a2a')
                weather_frame.pack(fill=tk.X, padx=10, pady=5)
                
                frames = {}
                frames['temp'] = tk.Label(weather_frame, text="", font=('Arial', config_en.FONT_SIZE_SMALL), fg='white', bg='#2a2a2a')
                frames['temp'].pack(anchor='w')
                
                frames['humidity'] = tk.Label(weather_frame, text="", font=('Arial', config_en.FONT_SIZE_SMALL), fg='white', bg='#2a2a2a')
                frames['humidity'].pack(anchor='w')
                
                frames['weather'] = tk.Label(weather_frame, text="", font=('Arial', config_en.FONT_SIZE_SMALL), fg='white', bg='#2a2a2a')
                frames['weather'].pack(anchor='w')
                
                # WBGT forecast table frame
                wbgt_frame = tk.LabelFrame(location_frame, text="📊 WBGT Forecast", 
                                         font=('Arial', config_en.FONT_SIZE_SMALL, 'bold'), fg='#00ccff', bg='#2a2a2a')
                wbgt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                # Create forecast table
                table_frame = tk.Frame(wbgt_frame, bg='#2a2a2a')
                table_frame.pack(fill='both', expand=True, padx=5, pady=5)
                
                # Create Treeview table for this location
                columns = ('time', 'value', 'level')
                location_forecast_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=4)
                
                # Configure column headers
                location_forecast_table.heading('time', text='Time')
                location_forecast_table.heading('value', text='WBGT')
                location_forecast_table.heading('level', text='Alert Level')
                
                # Configure column widths
                location_forecast_table.column('time', width=60, anchor='center')
                location_forecast_table.column('value', width=60, anchor='center')
                location_forecast_table.column('level', width=80, anchor='center')
                
                # Configure table style
                style = ttk.Style()
                style.theme_use('clam')
                style.configure('Treeview', background='#2a2a2a', foreground='white', 
                              fieldbackground='#2a2a2a', borderwidth=1)
                style.configure('Treeview.Heading', background='#404040', foreground='white',
                              borderwidth=1)
                style.map('Treeview', background=[('selected', '#505050')])
                
                location_forecast_table.pack(fill='both', expand=True)
                
                # Alert info frame
                alert_frame = tk.LabelFrame(location_frame, text="🚨 Heat Stroke Alert", 
                                          font=('Arial', config_en.FONT_SIZE_SMALL, 'bold'), fg='#00ccff', bg='#2a2a2a')
                alert_frame.pack(fill=tk.X, padx=10, pady=5)
                
                frames['today_alert'] = tk.Label(alert_frame, text="", font=('Arial', config_en.FONT_SIZE_SMALL), fg='white', bg='#2a2a2a')
                frames['today_alert'].pack(anchor='w')
                
                frames['tomorrow_alert'] = tk.Label(alert_frame, text="", font=('Arial', config_en.FONT_SIZE_SMALL), fg='white', bg='#2a2a2a')
                frames['tomorrow_alert'].pack(anchor='w')
                
                frames['forecast_table'] = location_forecast_table
                location_frames.append(frames)
            
            
            # Update time label
            update_time_label = tk.Label(
                main_frame,
                text="",
                font=('Arial', config_en.FONT_SIZE_SMALL),
                fg='gray',
                bg='black'
            )
            update_time_label.pack(side='bottom', pady=10)
            
            def get_wbgt_color(level):
                """Return color based on WBGT warning level"""
                colors = {
                    'Safe': '#0080ff',
                    'Caution': '#00ff00',
                    'Warning': '#ffff00',
                    'Severe Warning': '#ff8000',
                    'Dangerous': '#ff0000',
                    'Extremely Dangerous': '#800000'
                }
                return colors.get(level, '#ffffff')
            
            # Data update function
            def update_gui():
                try:
                    status_label.config(text="Updating data...", fg='yellow')
                    root.update()
                    
                    if self.update_data() and self.locations_data:
                        status_label.config(text="✅ Data updated successfully - Press ESC to exit", fg='green')
                        
                        # Update each location
                        for i, location_data in enumerate(self.locations_data):
                            if i < len(location_frames):
                                frames = location_frames[i]
                                weather_data = location_data.get('weather_data')
                                alert_data = location_data.get('alert_data')
                                
                                if weather_data:
                                    frames['temp'].config(text=f"🌡️ {weather_data['temperature']}°C", fg='yellow')
                                    frames['humidity'].config(text=f"💧 {weather_data['humidity']}%", fg='lightblue')
                                    frames['weather'].config(text=f"☁️ {weather_data['weather_description']}", fg='lightgreen')
                                    
                                    # Update WBGT forecast table
                                    forecast_table = frames['forecast_table']
                                    
                                    # Clear existing rows
                                    for item in forecast_table.get_children():
                                        forecast_table.delete(item)
                                    
                                    # Add current value
                                    current_data = location_data.get('env_wbgt_current')
                                    if current_data:
                                        level, _, _ = self.env_wbgt_api.get_wbgt_level_info(current_data['wbgt_value'])
                                        color = get_wbgt_color(level)
                                        item = forecast_table.insert('', 'end', values=('Current', f"{current_data['wbgt_value']:.1f}°C", level))
                                        forecast_table.set(item, 'level', level)
                                        # Apply color to row
                                        forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
                                        forecast_table.item(item, tags=(f'level_{level}',))
                                    
                                    # Add time series forecast values
                                    timeseries_data = location_data.get('env_wbgt_timeseries')
                                    if timeseries_data and 'timeseries' in timeseries_data:
                                        timeseries = timeseries_data['timeseries']
                                        # Show first 3 forecast values
                                        for j, data_point in enumerate(timeseries[:3]):
                                            level, _, _ = self.env_wbgt_api.get_wbgt_level_info(data_point['wbgt_value'])
                                            time_str = data_point['datetime_str']
                                            value_str = f"{data_point['wbgt_value']:.1f}°C"
                                            color = get_wbgt_color(level)
                                            item = forecast_table.insert('', 'end', values=(time_str, value_str, level))
                                            # Apply color to row
                                            forecast_table.tag_configure(f'level_{level}', background=color, foreground='black')
                                            forecast_table.item(item, tags=(f'level_{level}',))
                                
                                if alert_data and 'alerts' in alert_data:
                                    today_alert = alert_data['alerts']['today']
                                    tomorrow_alert = alert_data['alerts']['tomorrow']
                                    
                                    today_color = self.heatstroke_alert.get_alert_color(today_alert['level'])
                                    tomorrow_color = self.heatstroke_alert.get_alert_color(tomorrow_alert['level'])
                                    
                                    frames['today_alert'].config(text=f"Today: {today_alert['status']}", fg=today_color)
                                    frames['tomorrow_alert'].config(text=f"Tomorrow: {tomorrow_alert['status']}", fg=tomorrow_color)
                        
                        # Update time display
                        if self.locations_data and self.locations_data[0].get('weather_data'):
                            update_time = self.locations_data[0]['weather_data']['timestamp']
                            update_time_label.config(text=f"Last Updated: {update_time}")
                    
                    else:
                        status_label.config(text="Data fetch error - Press ESC to exit", fg='red')
                
                except Exception as e:
                    self.logger.error(f"GUI update error: {e}")
                    status_label.config(text=f"Display error: {e} - Press ESC to exit", fg='red')
                
                # Schedule next update
                root.after(config_en.UPDATE_INTERVAL_MINUTES * 60 * 1000, update_gui)
            
            # Initial update
            update_gui()
            
            # Start main loop
            self.logger.info("GUI mode kiosk application started")
            root.mainloop()
            
        except ImportError:
            print("❌ tkinter not available. Starting terminal mode.")
            self.run_terminal_mode()
        except Exception as e:
            print(f"❌ Error in GUI mode: {e}")
            print("Starting terminal mode.")
            self.run_terminal_mode()
        finally:
            self.logger.info("GUI mode kiosk application ended")
    
    def run(self):
        """Main execution"""
        try:
            if self.demo_mode:
                self.run_demo_mode()
            elif self.gui_mode:
                self.run_gui_mode()
            else:
                self.run_terminal_mode()
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"❌ Error: {e}")
            sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='WBGT Heat Stroke Warning Kiosk (English)')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    parser.add_argument('--gui', action='store_true', help='Run in GUI mode')
    
    args = parser.parse_args()
    
    kiosk = WBGTKioskEN(demo_mode=args.demo, gui_mode=args.gui)
    kiosk.run()

if __name__ == "__main__":
    main()