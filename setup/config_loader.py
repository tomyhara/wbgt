#!/usr/bin/env python3
"""
Configuration loader that supports both JSON and Python config files
Provides backward compatibility while adding JSON support
"""

import json
import os
from typing import Dict, Any, List

def load_config() -> Dict[str, Any]:
    """
    Load configuration from JSON file only
    Returns a standardized configuration dictionary
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_config_path = os.path.join(script_dir, 'config.json')
    
    # Try to load JSON config
    if os.path.exists(json_config_path):
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: Failed to load JSON config: {e}")
            print("Using default configuration...")
    else:
        # Create default JSON config if it doesn't exist
        print(f"Config file not found: {json_config_path}")
        print("Creating default configuration...")
        default_config = get_default_config()
        try:
            with open(json_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"Created default config file: {json_config_path}")
            return default_config
        except IOError as e:
            print(f"Warning: Failed to create config file: {e}")
    
    # Return default config if JSON loading fails
    return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Return default configuration"""
    return {
        "locations": [
            {
                "name": "横浜",
                "area_code": "140000",
                "wbgt_location_code": "46106",
                "prefecture": "神奈川県"
            },
            {
                "name": "銚子",
                "area_code": "120000",
                "wbgt_location_code": "45148",
                "prefecture": "千葉県"
            }
        ],
        "area_codes": {
            "札幌": "016000",
            "青森": "020000",
            "盛岡": "030000",
            "仙台": "040000",
            "秋田": "050000",
            "山形": "060000",
            "福島": "070000",
            "水戸": "080000",
            "宇都宮": "090000",
            "前橋": "100000",
            "さいたま": "110000",
            "千葉": "120000",
            "東京": "130000",
            "横浜": "140000",
            "新潟": "150000",
            "富山": "160000",
            "金沢": "170000",
            "福井": "180000",
            "甲府": "190000",
            "長野": "200000",
            "岐阜": "210000",
            "静岡": "220000",
            "名古屋": "230000",
            "津": "240000",
            "大津": "250000",
            "京都": "260000",
            "大阪": "270000",
            "神戸": "280000",
            "奈良": "290000",
            "和歌山": "300000",
            "鳥取": "310000",
            "松江": "320000",
            "岡山": "330000",
            "広島": "340000",
            "山口": "350000",
            "徳島": "360000",
            "高松": "370000",
            "松山": "380000",
            "高知": "390000",
            "福岡": "400000",
            "佐賀": "410000",
            "長崎": "420000",
            "熊本": "430000",
            "大分": "440000",
            "宮崎": "450000",
            "鹿児島": "460100",
            "那覇": "471000"
        },
        "update_interval_minutes": 30,
        "display": {
            "width": 800,
            "height": 600,
            "fullscreen": False
        },
        "font_sizes": {
            "large": 24,
            "medium": 18,
            "small": 14
        },
        "logging": {
            "level": "DEBUG",
            "file": "wbgt_kiosk.log"
        },
        "ssl": {
            "verify": True,
            "cert_path": None
        }
    }

def get_locations() -> List[Dict[str, Any]]:
    """Get configured locations"""
    config = load_config()
    return config.get('locations', [])

def get_area_codes() -> Dict[str, str]:
    """Get area codes mapping"""
    config = load_config()
    return config.get('area_codes', {})

# JSON-only configuration - no backward compatibility with Python config