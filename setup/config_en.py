# WBGT Heat Stroke Warning Kiosk Configuration (English Version)

# Monitoring Locations
# Multiple locations can be specified
LOCATIONS = [
    {
        'name': 'Yokohama',                    # Display name
        'area_code': '140000',                 # JMA area code
        'prefecture': 'Kanagawa',              # Prefecture name (for Environment Ministry API)
        'wbgt_location_code': '45132'          # Environment Ministry WBGT location code
    },
    {
        'name': 'Choshi',                      # Display name
        'area_code': '120000',                 # JMA area code
        'prefecture': 'Chiba',                 # Prefecture name (for Environment Ministry API)
        'wbgt_location_code': '44132'          # Environment Ministry WBGT location code
    }
]

# Update interval (minutes)
UPDATE_INTERVAL_MINUTES = 5

# GUI Settings (for experimental GUI version)
DISPLAY_WIDTH = 1024
DISPLAY_HEIGHT = 768
FONT_SIZE_LARGE = 20
FONT_SIZE_MEDIUM = 16
FONT_SIZE_SMALL = 12
FULLSCREEN = False

# ============================================
# Reference Information
# ============================================

# JMA Area Codes (Major Cities)
# Tokyo: 130000, Yokohama: 140000, Osaka: 270000, Nagoya: 230000
# Sapporo: 016000, Sendai: 040000, Hiroshima: 340000, Fukuoka: 400000
# 
# For complete list, refer to:
# https://www.jma.go.jp/jma/kishou/know/kurashi/koukei.html

# Environment Ministry WBGT Location Codes (Examples)
# Tokyo (Otemachi): 44132
# Yokohama: 45132
# Osaka: 47772
# Nagoya: 47636
# 
# For complete list, refer to:
# https://www.wbgt.env.go.jp/wbgt_data.php

# Prefecture Names (for Environment Ministry API)
# Must match exactly with Environment Ministry service prefecture notation
PREFECTURE_MAPPING = {
    'Hokkaido': 'hokkaido',
    'Aomori': 'aomori',
    'Iwate': 'iwate',
    'Miyagi': 'miyagi',
    'Akita': 'akita',
    'Yamagata': 'yamagata',
    'Fukushima': 'fukushima',
    'Ibaraki': 'ibaraki',
    'Tochigi': 'tochigi',
    'Gunma': 'gunma',
    'Saitama': 'saitama',
    'Chiba': 'chiba',
    'Tokyo': 'tokyo',
    'Kanagawa': 'kanagawa',
    'Niigata': 'niigata',
    'Toyama': 'toyama',
    'Ishikawa': 'ishikawa',
    'Fukui': 'fukui',
    'Yamanashi': 'yamanashi',
    'Nagano': 'nagano',
    'Gifu': 'gifu',
    'Shizuoka': 'shizuoka',
    'Aichi': 'aichi',
    'Mie': 'mie',
    'Shiga': 'shiga',
    'Kyoto': 'kyoto',
    'Osaka': 'osaka',
    'Hyogo': 'hyogo',
    'Nara': 'nara',
    'Wakayama': 'wakayama',
    'Tottori': 'tottori',
    'Shimane': 'shimane',
    'Okayama': 'okayama',
    'Hiroshima': 'hiroshima',
    'Yamaguchi': 'yamaguchi',
    'Tokushima': 'tokushima',
    'Kagawa': 'kagawa',
    'Ehime': 'ehime',
    'Kochi': 'kochi',
    'Fukuoka': 'fukuoka',
    'Saga': 'saga',
    'Nagasaki': 'nagasaki',
    'Kumamoto': 'kumamoto',
    'Oita': 'oita',
    'Miyazaki': 'miyazaki',
    'Kagoshima': 'kagoshima',
    'Okinawa': 'okinawa'
}