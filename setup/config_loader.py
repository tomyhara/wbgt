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
    Load configuration from JSON file with fallback to Python config
    Returns a standardized configuration dictionary
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to load JSON config first
    json_config_path = os.path.join(script_dir, 'config.json')
    if os.path.exists(json_config_path):
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load JSON config: {e}")
    
    # Fallback to Python config
    try:
        import config
        return {
            "locations": getattr(config, 'LOCATIONS', []),
            "area_codes": getattr(config, 'AREA_CODES', {}),
            "update_interval_minutes": getattr(config, 'UPDATE_INTERVAL_MINUTES', 30),
            "display": {
                "width": getattr(config, 'DISPLAY_WIDTH', 800),
                "height": getattr(config, 'DISPLAY_HEIGHT', 600),
                "fullscreen": getattr(config, 'FULLSCREEN', False)
            },
            "font_sizes": {
                "large": getattr(config, 'FONT_SIZE_LARGE', 24),
                "medium": getattr(config, 'FONT_SIZE_MEDIUM', 18),
                "small": getattr(config, 'FONT_SIZE_SMALL', 14)
            },
            "logging": {
                "level": getattr(config, 'LOG_LEVEL', 'INFO'),
                "file": getattr(config, 'LOG_FILE', 'wbgt_kiosk.log')
            },
            "ssl": {
                "verify": getattr(config, 'SSL_VERIFY', True),
                "cert_path": getattr(config, 'SSL_CERT_PATH', None)
            }
        }
    except ImportError as e:
        print(f"Warning: Failed to load Python config: {e}")
    
    # Return default config if both fail
    return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Return default configuration"""
    return {
        "locations": [
            {
                "name": "東京",
                "area_code": "130000",
                "wbgt_location_code": "44132",
                "prefecture": "東京都"
            }
        ],
        "area_codes": {
            "東京": "130000"
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
            "level": "INFO",
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

# Backward compatibility - expose variables that existing code expects
try:
    _config = load_config()
    LOCATIONS = _config.get('locations', [])
    AREA_CODES = _config.get('area_codes', {})
    UPDATE_INTERVAL_MINUTES = _config.get('update_interval_minutes', 30)
    DISPLAY_WIDTH = _config.get('display', {}).get('width', 800)
    DISPLAY_HEIGHT = _config.get('display', {}).get('height', 600)
    FULLSCREEN = _config.get('display', {}).get('fullscreen', False)
    FONT_SIZE_LARGE = _config.get('font_sizes', {}).get('large', 24)
    FONT_SIZE_MEDIUM = _config.get('font_sizes', {}).get('medium', 18)
    FONT_SIZE_SMALL = _config.get('font_sizes', {}).get('small', 14)
    LOG_LEVEL = _config.get('logging', {}).get('level', 'INFO')
    LOG_FILE = _config.get('logging', {}).get('file', 'wbgt_kiosk.log')
    SSL_VERIFY = _config.get('ssl', {}).get('verify', True)
    SSL_CERT_PATH = _config.get('ssl', {}).get('cert_path', None)
except Exception as e:
    print(f"Warning: Error loading config: {e}")
    _default = get_default_config()
    LOCATIONS = _default['locations']
    AREA_CODES = _default['area_codes']
    UPDATE_INTERVAL_MINUTES = _default['update_interval_minutes']
    DISPLAY_WIDTH = _default['display']['width']
    DISPLAY_HEIGHT = _default['display']['height']
    FULLSCREEN = _default['display']['fullscreen']
    FONT_SIZE_LARGE = _default['font_sizes']['large']
    FONT_SIZE_MEDIUM = _default['font_sizes']['medium']
    FONT_SIZE_SMALL = _default['font_sizes']['small']
    LOG_LEVEL = _default['logging']['level']
    LOG_FILE = _default['logging']['file']
    SSL_VERIFY = _default['ssl']['verify']
    SSL_CERT_PATH = _default['ssl']['cert_path']