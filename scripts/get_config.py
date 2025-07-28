#!/usr/bin/env python3
"""
Configuration reader for bash scripts
Reads config.json or falls back to config.py and outputs area codes and locations
"""

import json
import os
import sys

def get_script_dir():
    """Get the directory where this script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """Load configuration from JSON or Python config file"""
    script_dir = get_script_dir()
    config_dir = os.path.join(script_dir, '..', 'setup')
    
    # Try JSON config first
    json_config_path = os.path.join(config_dir, 'config.json')
    if os.path.exists(json_config_path):
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load JSON config: {e}", file=sys.stderr)
    
    # Fallback to Python config
    sys.path.insert(0, config_dir)
    try:
        import config
        return {
            "locations": getattr(config, 'LOCATIONS', []),
            "area_codes": getattr(config, 'AREA_CODES', {}),
        }
    except ImportError as e:
        print(f"Warning: Failed to load Python config: {e}", file=sys.stderr)
    
    # Return empty config if both fail
    return {"locations": [], "area_codes": {}}

def main():
    """Main function - outputs configuration based on command line argument"""
    if len(sys.argv) < 2:
        print("Usage: python3 get_config.py [area_codes|locations|prefectures]", file=sys.stderr)
        sys.exit(1)
    
    config = load_config()
    output_type = sys.argv[1]
    
    if output_type == "area_codes":
        # Output area codes from locations
        locations = config.get('locations', [])
        for location in locations:
            area_code = location.get('area_code', '')
            name = location.get('name', '')
            if area_code:
                print(f"{area_code}:{name}")
    
    elif output_type == "locations":
        # Output locations as JSON for easier parsing
        locations = config.get('locations', [])
        print(json.dumps(locations, ensure_ascii=False))
    
    elif output_type == "prefectures":
        # Output prefectures for WBGT download (mapping common prefecture names)
        prefecture_mapping = {
            "東京都": "tokyo",
            "神奈川県": "kanagawa",
            "大阪府": "osaka",
            "愛知県": "aichi",
            "福岡県": "fukuoka",
            "北海道": "hokkaido",
            "宮城県": "miyagi",
            "千葉県": "chiba",
        }
        
        locations = config.get('locations', [])
        prefectures = set()
        
        for location in locations:
            prefecture = location.get('prefecture', '')
            if prefecture in prefecture_mapping:
                prefectures.add(prefecture_mapping[prefecture])
        
        # If no prefectures found from config, add defaults
        if not prefectures:
            default_prefectures = ["tokyo", "kanagawa", "osaka", "aichi", "fukuoka", "hokkaido", "miyagi"]
            prefectures.update(default_prefectures)
        
        for prefecture in sorted(prefectures):
            print(prefecture)
    
    else:
        print(f"Unknown output type: {output_type}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()