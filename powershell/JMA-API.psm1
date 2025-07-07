# JMA (Japan Meteorological Agency) API Client Module
# PowerShell Version - English

# Import configuration
. "$PSScriptRoot\config.ps1"

# Initialize configuration
$Config = Get-Config

# Weather code to conditions mapping
$script:WEATHER_CODE_MAP = @{
    "100" = @{ "Weather" = "Sunny"; "TempAdj" = 3; "HumidityAdj" = -10 }
    "101" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 2; "HumidityAdj" = -5 }
    "102" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 1; "HumidityAdj" = 0 }
    "103" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 1; "HumidityAdj" = 0 }
    "104" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "105" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "106" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "107" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "108" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "110" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "111" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "112" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "113" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "114" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "115" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "116" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "117" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "118" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "119" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "120" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "121" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "122" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "123" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "124" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "125" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "126" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "127" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "128" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "130" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "131" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "132" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "140" = @{ "Weather" = "Partly Cloudy"; "TempAdj" = 0; "HumidityAdj" = 5 }
    "200" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 10 }
    "201" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 10 }
    "202" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "203" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "204" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "205" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "206" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "207" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "208" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "209" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "210" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "211" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "212" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "213" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "214" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "215" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "218" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "219" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "220" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "221" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "222" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "223" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "224" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "225" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "226" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "228" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "229" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "230" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "231" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "240" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "250" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "260" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "270" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "281" = @{ "Weather" = "Cloudy"; "TempAdj" = -1; "HumidityAdj" = 15 }
    "300" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "301" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "302" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "303" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "304" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "306" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "308" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "309" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "311" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "313" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "314" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "315" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "316" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "317" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "320" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "321" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "322" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "323" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "324" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "325" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "326" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "327" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "328" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "329" = @{ "Weather" = "Rainy"; "TempAdj" = -3; "HumidityAdj" = 25 }
    "340" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "350" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "361" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "371" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "400" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "401" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "402" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "403" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "405" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "406" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "407" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "409" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "411" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "413" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "414" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "420" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "421" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "422" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "423" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "425" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "426" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "427" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
    "450" = @{ "Weather" = "Snowy"; "TempAdj" = -5; "HumidityAdj" = 30 }
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "INFO" { Write-Host $logEntry -ForegroundColor White }
        "DEBUG" { Write-Host $logEntry -ForegroundColor Gray }
        default { Write-Host $logEntry }
    }
    
    # Write to file
    try {
        Add-Content -Path $Config.LOG_FILE -Value $logEntry -Encoding UTF8
    }
    catch {
        Write-Host "Failed to write to log file: $_" -ForegroundColor Red
    }
}

function Get-CurrentWeather {
    param(
        [string]$AreaCode
    )
    
    try {
        $url = "$($Config.JMA_API_BASE_URL)/$AreaCode.json"
        Write-Log "Fetching weather data from: $url" "DEBUG"
        
        $headers = @{
            "User-Agent" = $Config.USER_AGENT
        }
        
        $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers -TimeoutSec $Config.REQUEST_TIMEOUT
        
        if (-not $response) {
            throw "Empty response from JMA API"
        }
        
        # Extract current weather data
        $currentWeather = $response[0]
        if (-not $currentWeather.timeSeries) {
            throw "No timeSeries data in response"
        }
        
        $timeSeries = $currentWeather.timeSeries[0]
        $areas = $timeSeries.areas[0]
        
        # Get weather code
        $weatherCode = $null
        if ($areas.weatherCodes -and $areas.weatherCodes.Count -gt 0) {
            $weatherCode = $areas.weatherCodes[0]
        }
        
        # Get temperatures
        $tempSeries = $null
        foreach ($series in $currentWeather.timeSeries) {
            if ($series.areas[0].temps) {
                $tempSeries = $series
                break
            }
        }
        
        $temperature = 25  # Default temperature
        if ($tempSeries -and $tempSeries.areas[0].temps -and $tempSeries.areas[0].temps.Count -gt 0) {
            $temperature = [int]$tempSeries.areas[0].temps[0]
        }
        
        # Estimate humidity based on weather conditions
        $humidity = 60  # Default humidity
        $weatherCondition = "Unknown"
        
        if ($weatherCode -and $script:WEATHER_CODE_MAP.ContainsKey($weatherCode)) {
            $weatherInfo = $script:WEATHER_CODE_MAP[$weatherCode]
            $weatherCondition = $weatherInfo.Weather
            $temperature += $weatherInfo.TempAdj
            $humidity += $weatherInfo.HumidityAdj
        }
        
        # Apply seasonal adjustments
        $currentMonth = (Get-Date).Month
        if ($currentMonth -ge 6 -and $currentMonth -le 8) {
            # Summer months - higher humidity
            $humidity += 10
        } elseif ($currentMonth -ge 12 -or $currentMonth -le 2) {
            # Winter months - lower humidity
            $humidity -= 15
        }
        
        # Ensure humidity is within reasonable bounds
        $humidity = [Math]::Max(20, [Math]::Min(95, $humidity))
        
        $result = @{
            "temperature" = $temperature
            "humidity" = $humidity
            "weather_condition" = $weatherCondition
            "weather_code" = $weatherCode
            "feels_like" = Calculate-FeelsLike -Temperature $temperature -Humidity $humidity
            "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            "source" = "JMA API"
        }
        
        Write-Log "Weather data retrieved successfully: Temp=$temperature°C, Humidity=$humidity%, Weather=$weatherCondition" "INFO"
        return $result
    }
    catch {
        Write-Log "Error fetching weather data: $_" "ERROR"
        throw $_
    }
}

function Calculate-FeelsLike {
    param(
        [double]$Temperature,
        [double]$Humidity
    )
    
    # Simple heat index calculation
    $T = $Temperature
    $RH = $Humidity
    
    if ($T -ge 27) {
        # Heat index formula for temperatures above 27°C
        $HI = -8.78469475556 + 1.61139411 * $T + 2.33854883889 * $RH - 0.14611605 * $T * $RH - 0.012308094 * $T * $T - 0.0164248277778 * $RH * $RH + 0.002211732 * $T * $T * $RH + 0.00072546 * $T * $RH * $RH - 0.000003582 * $T * $T * $RH * $RH
        return [Math]::Round($HI, 1)
    } else {
        # For lower temperatures, feels like is approximately the same as actual temperature
        return [Math]::Round($T, 1)
    }
}

function Calculate-WBGT {
    param(
        [double]$Temperature,
        [double]$Humidity,
        [double]$GlobalTemp = $null
    )
    
    # WBGT calculation for outdoor conditions without black globe temperature
    # Simplified formula: WBGT = 0.7 * Tw + 0.3 * Ta
    # Where Tw is wet bulb temperature, Ta is dry bulb temperature
    
    $wetBulbTemp = Calculate-WetBulbTemperature -Temperature $Temperature -Humidity $Humidity
    $wbgt = 0.7 * $wetBulbTemp + 0.3 * $Temperature
    
    return [Math]::Round($wbgt, 1)
}

function Calculate-WetBulbTemperature {
    param(
        [double]$Temperature,
        [double]$Humidity
    )
    
    # Approximation of wet bulb temperature
    $T = $Temperature
    $RH = $Humidity / 100.0
    
    # Stull's formula (simplified)
    $Tw = $T * [Math]::Atan(0.151977 * [Math]::Pow(($RH * 100 + 8.313659), 0.5)) + [Math]::Atan($T + $RH * 100) - [Math]::Atan($RH * 100 - 1.676331) + 0.00391838 * [Math]::Pow(($RH * 100), 1.5) * [Math]::Atan(0.023101 * $RH * 100) - 4.686035
    
    return [Math]::Round($Tw, 1)
}

function Get-WBGTLevel {
    param(
        [double]$WBGTValue
    )
    
    foreach ($level in $Config.WBGT_LEVELS.GetEnumerator()) {
        if ($WBGTValue -lt $level.Value.THRESHOLD) {
            return $level.Value
        }
    }
    
    # Return highest level if WBGT is very high
    return $Config.WBGT_LEVELS.DANGER
}

function Get-WeatherCondition {
    param(
        [string]$WeatherCode
    )
    
    if ($script:WEATHER_CODE_MAP.ContainsKey($WeatherCode)) {
        return $script:WEATHER_CODE_MAP[$WeatherCode].Weather
    }
    
    return "Unknown"
}

# Export functions
Export-ModuleMember -Function Get-CurrentWeather, Calculate-WBGT, Get-WBGTLevel, Calculate-FeelsLike, Get-WeatherCondition