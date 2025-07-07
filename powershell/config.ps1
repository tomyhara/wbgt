# WBGT Heat Stroke Warning Kiosk Configuration
# PowerShell Version - English

# Location Configuration
$script:LOCATIONS = @(
    @{
        AREA_CODE = "130000"
        CITY_NAME = "Tokyo"
        WBGT_CODE = "13"
        PREFECTURE_NAME = "Tokyo"
    },
    @{
        AREA_CODE = "270000"
        CITY_NAME = "Osaka"
        WBGT_CODE = "27"
        PREFECTURE_NAME = "Osaka"
    },
    @{
        AREA_CODE = "230000"
        CITY_NAME = "Nagoya"
        WBGT_CODE = "23"
        PREFECTURE_NAME = "Aichi"
    },
    @{
        AREA_CODE = "140000"
        CITY_NAME = "Yokohama"
        WBGT_CODE = "14"
        PREFECTURE_NAME = "Kanagawa"
    }
)

# Update Interval (minutes)
$script:UPDATE_INTERVAL_MINUTES = 30

# Demo Mode Settings
$script:DEMO_CYCLES = 3
$script:DEMO_INTERVAL_SECONDS = 5

# Display Settings
$script:CONSOLE_WIDTH = 120
$script:CONSOLE_HEIGHT = 40

# Logging Configuration
$script:LOG_FILE = "wbgt_kiosk.log"
$script:LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
$script:LOG_MAX_SIZE_MB = 10
$script:LOG_BACKUP_COUNT = 5

# SSL Configuration for Corporate Environments
$script:SSL_VERIFY = $true
$script:SSL_CERT_PATH = ""
$script:SSL_KEY_PATH = ""

# API Configuration
$script:JMA_API_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast"
$script:ENV_WBGT_BASE_URL = "https://www.wbgt.env.go.jp/graph_ref_td.php"
$script:ENV_ALERT_BASE_URL = "https://www.wbgt.env.go.jp/alert_graph_ref_td.php"

# User Agent for API Requests
$script:USER_AGENT = "WBGT-Kiosk-PowerShell/1.0"

# Request Timeout (seconds)
$script:REQUEST_TIMEOUT = 30

# Prefecture Name to Code Mapping for Environment Ministry API
$script:PREFECTURE_MAPPING = @{
    "Hokkaido" = "01"
    "Aomori" = "02"
    "Iwate" = "03"
    "Miyagi" = "04"
    "Akita" = "05"
    "Yamagata" = "06"
    "Fukushima" = "07"
    "Ibaraki" = "08"
    "Tochigi" = "09"
    "Gunma" = "10"
    "Saitama" = "11"
    "Chiba" = "12"
    "Tokyo" = "13"
    "Kanagawa" = "14"
    "Niigata" = "15"
    "Toyama" = "16"
    "Ishikawa" = "17"
    "Fukui" = "18"
    "Yamanashi" = "19"
    "Nagano" = "20"
    "Gifu" = "21"
    "Shizuoka" = "22"
    "Aichi" = "23"
    "Mie" = "24"
    "Shiga" = "25"
    "Kyoto" = "26"
    "Osaka" = "27"
    "Hyogo" = "28"
    "Nara" = "29"
    "Wakayama" = "30"
    "Tottori" = "31"
    "Shimane" = "32"
    "Okayama" = "33"
    "Hiroshima" = "34"
    "Yamaguchi" = "35"
    "Tokushima" = "36"
    "Kagawa" = "37"
    "Ehime" = "38"
    "Kochi" = "39"
    "Fukuoka" = "40"
    "Saga" = "41"
    "Nagasaki" = "42"
    "Kumamoto" = "43"
    "Oita" = "44"
    "Miyazaki" = "45"
    "Kagoshima" = "46"
    "Okinawa" = "47"
}

# Area Code to City Name Mapping
$script:AREA_CODE_MAPPING = @{
    "011000" = "Sapporo"
    "012000" = "Kushiro"
    "013000" = "Nemuro"
    "014030" = "Hakodate"
    "014100" = "Muroran"
    "015000" = "Tomakomai"
    "016000" = "Obihiro"
    "017000" = "Kitami"
    "018000" = "Nayoro"
    "019000" = "Wakkanai"
    "020000" = "Aomori"
    "030000" = "Morioka"
    "040000" = "Sendai"
    "050000" = "Akita"
    "060000" = "Yamagata"
    "070000" = "Fukushima"
    "080000" = "Mito"
    "090000" = "Utsunomiya"
    "100000" = "Maebashi"
    "110000" = "Saitama"
    "120000" = "Chiba"
    "130000" = "Tokyo"
    "140000" = "Yokohama"
    "150000" = "Niigata"
    "160000" = "Toyama"
    "170000" = "Kanazawa"
    "180000" = "Fukui"
    "190000" = "Kofu"
    "200000" = "Nagano"
    "210000" = "Gifu"
    "220000" = "Shizuoka"
    "230000" = "Nagoya"
    "240000" = "Tsu"
    "250000" = "Otsu"
    "260000" = "Kyoto"
    "270000" = "Osaka"
    "280000" = "Kobe"
    "290000" = "Nara"
    "300000" = "Wakayama"
    "310000" = "Tottori"
    "320000" = "Matsue"
    "330000" = "Okayama"
    "340000" = "Hiroshima"
    "350000" = "Yamaguchi"
    "360000" = "Tokushima"
    "370000" = "Takamatsu"
    "380000" = "Matsuyama"
    "390000" = "Kochi"
    "400000" = "Fukuoka"
    "410000" = "Saga"
    "420000" = "Nagasaki"
    "430000" = "Kumamoto"
    "440000" = "Oita"
    "450000" = "Miyazaki"
    "460100" = "Kagoshima"
    "471000" = "Naha"
    "472000" = "Miyakojima"
    "473000" = "Ishigakijima"
}

# WBGT Warning Levels
$script:WBGT_LEVELS = @{
    "SAFE" = @{
        "THRESHOLD" = 21
        "LEVEL" = "Almost Safe"
        "COLOR" = "White"
        "ADVICE" = "Generally safe for outdoor activities"
    }
    "CAUTION" = @{
        "THRESHOLD" = 25
        "LEVEL" = "Caution"
        "COLOR" = "Yellow"
        "ADVICE" = "Hydrate regularly during outdoor activities"
    }
    "WARNING" = @{
        "THRESHOLD" = 28
        "LEVEL" = "Warning"
        "COLOR" = "DarkYellow"
        "ADVICE" = "Take frequent breaks and stay hydrated"
    }
    "SEVERE_WARNING" = @{
        "THRESHOLD" = 31
        "LEVEL" = "Severe Warning"
        "COLOR" = "Red"
        "ADVICE" = "Avoid strenuous outdoor activities"
    }
    "DANGER" = @{
        "THRESHOLD" = 999
        "LEVEL" = "Danger"
        "COLOR" = "DarkRed"
        "ADVICE" = "Avoid all outdoor activities"
    }
}

# Heat Stroke Alert Levels
$script:ALERT_LEVELS = @{
    0 = @{
        "LEVEL" = "No Alert"
        "COLOR" = "Gray"
        "DESCRIPTION" = "No heat stroke alert issued"
    }
    1 = @{
        "LEVEL" = "Alert"
        "COLOR" = "Red"
        "DESCRIPTION" = "Heat stroke alert issued"
    }
}

# Color Configuration for Console Output
$script:COLORS = @{
    "HEADER" = "Cyan"
    "INFO" = "White"
    "WARNING" = "Yellow"
    "ERROR" = "Red"
    "SUCCESS" = "Green"
    "TEMPERATURE" = "Yellow"
    "HUMIDITY" = "Cyan"
    "WBGT" = "Magenta"
    "ALERT" = "Red"
    "TIMESTAMP" = "Gray"
}

# Export configuration variables
function Get-Config {
    return @{
        LOCATIONS = $script:LOCATIONS
        UPDATE_INTERVAL_MINUTES = $script:UPDATE_INTERVAL_MINUTES
        DEMO_CYCLES = $script:DEMO_CYCLES
        DEMO_INTERVAL_SECONDS = $script:DEMO_INTERVAL_SECONDS
        CONSOLE_WIDTH = $script:CONSOLE_WIDTH
        CONSOLE_HEIGHT = $script:CONSOLE_HEIGHT
        LOG_FILE = $script:LOG_FILE
        LOG_LEVEL = $script:LOG_LEVEL
        LOG_MAX_SIZE_MB = $script:LOG_MAX_SIZE_MB
        LOG_BACKUP_COUNT = $script:LOG_BACKUP_COUNT
        SSL_VERIFY = $script:SSL_VERIFY
        SSL_CERT_PATH = $script:SSL_CERT_PATH
        SSL_KEY_PATH = $script:SSL_KEY_PATH
        JMA_API_BASE_URL = $script:JMA_API_BASE_URL
        ENV_WBGT_BASE_URL = $script:ENV_WBGT_BASE_URL
        ENV_ALERT_BASE_URL = $script:ENV_ALERT_BASE_URL
        USER_AGENT = $script:USER_AGENT
        REQUEST_TIMEOUT = $script:REQUEST_TIMEOUT
        PREFECTURE_MAPPING = $script:PREFECTURE_MAPPING
        AREA_CODE_MAPPING = $script:AREA_CODE_MAPPING
        WBGT_LEVELS = $script:WBGT_LEVELS
        ALERT_LEVELS = $script:ALERT_LEVELS
        COLORS = $script:COLORS
    }
}

# Helper function to get area code by city name
function Get-AreaCodeByCity {
    param([string]$CityName)
    
    foreach ($area in $script:AREA_CODE_MAPPING.GetEnumerator()) {
        if ($area.Value -eq $CityName) {
            return $area.Key
        }
    }
    return $null
}

# Helper function to get prefecture code by name
function Get-PrefectureCode {
    param([string]$PrefectureName)
    
    return $script:PREFECTURE_MAPPING[$PrefectureName]
}