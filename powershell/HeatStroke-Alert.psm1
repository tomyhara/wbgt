# Heat Stroke Alert Module
# PowerShell Version - English

# Import required modules
Import-Module "$PSScriptRoot\JMA-API.psm1" -Force
Import-Module "$PSScriptRoot\ENV-WBGT-API.psm1" -Force

# Import configuration
. "$PSScriptRoot\config.ps1"

# Initialize configuration
$Config = Get-Config

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

function Get-AlertData {
    param(
        [string]$AreaCode,
        [string]$PrefectureCode
    )
    
    Write-Log "Fetching alert data for area: $AreaCode, prefecture: $PrefectureCode" "INFO"
    
    # First, try to get official alert data from Environment Ministry
    $officialAlert = $null
    if (Test-ServiceAvailable) {
        Write-Log "Environment Ministry service is available, fetching official alert data" "DEBUG"
        $officialAlert = Get-AlertData -PrefectureCode $PrefectureCode
    } else {
        Write-Log "Environment Ministry service is not available, will use JMA API estimation" "WARNING"
    }
    
    # If official data is available, use it
    if ($officialAlert) {
        Write-Log "Using official alert data from Environment Ministry" "INFO"
        return @{
            "today" = $officialAlert.today
            "tomorrow" = $officialAlert.tomorrow
            "today_level" = Get-AlertLevel -AlertValue $officialAlert.today
            "tomorrow_level" = Get-AlertLevel -AlertValue $officialAlert.tomorrow
            "source" = "Environment Ministry (Official)"
            "timestamp" = $officialAlert.timestamp
        }
    }
    
    # Fallback to JMA API estimation
    Write-Log "Falling back to JMA API estimation for alert data" "INFO"
    try {
        $weatherData = Get-CurrentWeather -AreaCode $AreaCode
        if (-not $weatherData) {
            throw "Failed to get weather data for alert estimation"
        }
        
        # Calculate WBGT for alert estimation
        $wbgtValue = Calculate-WBGT -Temperature $weatherData.temperature -Humidity $weatherData.humidity
        $wbgtLevel = Get-WBGTLevel -WBGTValue $wbgtValue
        
        # Estimate alert level based on WBGT
        $alertLevel = 0
        if ($wbgtValue -ge 28) {
            $alertLevel = 1  # Issue alert for WBGT >= 28
        }
        
        Write-Log "Estimated alert level: $alertLevel (WBGT: $wbgtValue°C)" "INFO"
        
        return @{
            "today" = $alertLevel
            "tomorrow" = $alertLevel  # Use same level for tomorrow (estimation)
            "today_level" = Get-AlertLevel -AlertValue $alertLevel
            "tomorrow_level" = Get-AlertLevel -AlertValue $alertLevel
            "source" = "JMA API (Estimated)"
            "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            "wbgt_value" = $wbgtValue
        }
    }
    catch {
        Write-Log "Error estimating alert data: $_" "ERROR"
        
        # Return default no-alert data
        return @{
            "today" = 0
            "tomorrow" = 0
            "today_level" = Get-AlertLevel -AlertValue 0
            "tomorrow_level" = Get-AlertLevel -AlertValue 0
            "source" = "Default (Error fallback)"
            "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            "error" = $_.Exception.Message
        }
    }
}

function Get-EstimatedAlertFromWeather {
    param(
        [string]$WeatherCode,
        [double]$Temperature,
        [double]$Humidity
    )
    
    # Weather-based alert estimation
    $alertLevel = 0
    
    # High temperature threshold
    if ($Temperature -gt 35) {
        $alertLevel = 1
    } elseif ($Temperature -gt 30 -and $Humidity -gt 70) {
        $alertLevel = 1
    }
    
    # Weather condition adjustments
    if ($WeatherCode) {
        $weatherCondition = Get-WeatherCondition -WeatherCode $WeatherCode
        
        switch ($weatherCondition) {
            "Sunny" {
                if ($Temperature -gt 28) {
                    $alertLevel = 1
                }
            }
            "Partly Cloudy" {
                if ($Temperature -gt 30) {
                    $alertLevel = 1
                }
            }
            "Cloudy" {
                if ($Temperature -gt 32) {
                    $alertLevel = 1
                }
            }
            "Rainy" {
                if ($Temperature -gt 28 -and $Humidity -gt 80) {
                    $alertLevel = 1
                }
            }
        }
    }
    
    return $alertLevel
}

function Get-AlertLevelDescription {
    param(
        [int]$AlertValue
    )
    
    $alertInfo = Get-AlertLevel -AlertValue $AlertValue
    
    switch ($AlertValue) {
        0 {
            return @{
                "level" = $alertInfo.LEVEL
                "color" = $alertInfo.COLOR
                "description" = $alertInfo.DESCRIPTION
                "advice" = "Normal outdoor activities are generally safe. Stay hydrated and monitor weather conditions."
            }
        }
        1 {
            return @{
                "level" = $alertInfo.LEVEL
                "color" = $alertInfo.COLOR
                "description" = $alertInfo.DESCRIPTION
                "advice" = "High risk of heat stroke. Avoid strenuous outdoor activities. Stay in air-conditioned areas, drink water frequently, and take frequent breaks."
            }
        }
        default {
            return @{
                "level" = "Unknown"
                "color" = "Gray"
                "description" = "Unknown alert level"
                "advice" = "Monitor weather conditions and stay hydrated."
            }
        }
    }
}

function Format-AlertDisplay {
    param(
        [hashtable]$AlertData
    )
    
    $todayInfo = Get-AlertLevelDescription -AlertValue $AlertData.today
    $tomorrowInfo = Get-AlertLevelDescription -AlertValue $AlertData.tomorrow
    
    $output = @"

═══════════════════════════════════════════════════════════════════════════════
                            🚨 HEAT STROKE ALERTS 🚨
═══════════════════════════════════════════════════════════════════════════════

📅 TODAY'S ALERT:      $($todayInfo.level)
📅 TOMORROW'S ALERT:   $($tomorrowInfo.level)

🔍 DATA SOURCE:        $($AlertData.source)
🕒 LAST UPDATED:       $($AlertData.timestamp)

"@

    Write-Host $output

    # Display today's alert with color
    Write-Host "📅 TODAY'S STATUS:" -ForegroundColor White -NoNewline
    Write-Host "    $($todayInfo.level)" -ForegroundColor $todayInfo.color
    Write-Host "   $($todayInfo.description)" -ForegroundColor Gray
    Write-Host "   💡 $($todayInfo.advice)" -ForegroundColor Cyan
    Write-Host ""
    
    # Display tomorrow's alert with color
    Write-Host "📅 TOMORROW'S STATUS:" -ForegroundColor White -NoNewline
    Write-Host " $($tomorrowInfo.level)" -ForegroundColor $tomorrowInfo.color
    Write-Host "   $($tomorrowInfo.description)" -ForegroundColor Gray
    Write-Host "   💡 $($tomorrowInfo.advice)" -ForegroundColor Cyan
    
    if ($AlertData.wbgt_value) {
        Write-Host ""
        Write-Host "🌡️  ESTIMATED WBGT: $($AlertData.wbgt_value)°C" -ForegroundColor Magenta
    }
    
    if ($AlertData.error) {
        Write-Host ""
        Write-Host "⚠️  ERROR: $($AlertData.error)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════════"
}

function Get-AlertSummary {
    param(
        [hashtable]$AlertData
    )
    
    $todayLevel = Get-AlertLevelDescription -AlertValue $AlertData.today
    $tomorrowLevel = Get-AlertLevelDescription -AlertValue $AlertData.tomorrow
    
    return @{
        "today" = @{
            "level" = $AlertData.today
            "status" = $todayLevel.level
            "color" = $todayLevel.color
            "description" = $todayLevel.description
            "advice" = $todayLevel.advice
        }
        "tomorrow" = @{
            "level" = $AlertData.tomorrow
            "status" = $tomorrowLevel.level
            "color" = $tomorrowLevel.color
            "description" = $tomorrowLevel.description
            "advice" = $tomorrowLevel.advice
        }
        "source" = $AlertData.source
        "timestamp" = $AlertData.timestamp
    }
}

# Export functions
Export-ModuleMember -Function Get-AlertData, Get-AlertLevelDescription, Format-AlertDisplay, Get-AlertSummary, Get-EstimatedAlertFromWeather