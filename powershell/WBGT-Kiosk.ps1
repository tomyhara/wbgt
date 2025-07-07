# WBGT Heat Stroke Warning Kiosk
# PowerShell Version - English
# Author: WBGT Kiosk PowerShell Edition
# Version: 1.0.0

param(
    [switch]$Demo,
    [switch]$Help,
    [int]$Cycles = 0,
    [int]$IntervalMinutes = 0
)

# Script directory
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Import required modules
Import-Module "$ScriptDirectory\JMA-API.psm1" -Force
Import-Module "$ScriptDirectory\ENV-WBGT-API.psm1" -Force
Import-Module "$ScriptDirectory\HeatStroke-Alert.psm1" -Force

# Import configuration
. "$ScriptDirectory\config.ps1"

# Initialize configuration
$Config = Get-Config

# Global variables for script control
$script:IsRunning = $true
$script:CycleCount = 0
$script:StartTime = Get-Date

function Show-Help {
    $helpText = @"

═══════════════════════════════════════════════════════════════════════════════
                    🌡️  WBGT Heat Stroke Warning Kiosk  🌡️
═══════════════════════════════════════════════════════════════════════════════

DESCRIPTION:
    PowerShell-based WBGT (Wet Bulb Globe Temperature) monitoring kiosk that
    displays real-time heat stroke warnings and weather information from
    Japanese meteorological services.

USAGE:
    .\WBGT-Kiosk.ps1 [OPTIONS]

OPTIONS:
    -Demo                   Run in demo mode (3 cycles, 5-second intervals)
    -Help                   Show this help message
    -Cycles <number>        Number of update cycles (0 = infinite)
    -IntervalMinutes <min>  Update interval in minutes (default: 30)

EXAMPLES:
    .\WBGT-Kiosk.ps1                           # Normal operation
    .\WBGT-Kiosk.ps1 -Demo                     # Demo mode
    .\WBGT-Kiosk.ps1 -Cycles 5                 # Run 5 cycles then exit
    .\WBGT-Kiosk.ps1 -IntervalMinutes 15       # Update every 15 minutes

FEATURES:
    🌤️  Real-time weather information from JMA API
    🌡️  WBGT index display with official Environment Ministry data
    🚨  Heat stroke alerts for today and tomorrow
    🎯  Data source indication (Official/Estimated)
    🎨  Color-coded warning levels
    🔄  Automatic updates every 30 minutes
    📅  Seasonal service availability detection

DATA SOURCES:
    - Environment Ministry WBGT Service (Official, April 23 - October 22)
    - Japan Meteorological Agency API (Weather data and fallback WBGT)

CONTROLS:
    Ctrl+C              Exit the application
    
CONFIGURATION:
    Edit config.ps1 to modify locations, update intervals, and other settings.

═══════════════════════════════════════════════════════════════════════════════

"@
    Write-Host $helpText -ForegroundColor Cyan
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console based on log level
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

function Initialize-Console {
    # Set console title
    $Host.UI.RawUI.WindowTitle = "WBGT Heat Stroke Warning Kiosk - PowerShell Edition"
    
    # Clear console
    Clear-Host
    
    # Set console size if possible
    try {
        $Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size($Config.CONSOLE_WIDTH, 200)
        $Host.UI.RawUI.WindowSize = New-Object Management.Automation.Host.Size($Config.CONSOLE_WIDTH, $Config.CONSOLE_HEIGHT)
    }
    catch {
        Write-Log "Could not set console size: $_" "WARNING"
    }
}

function Show-Banner {
    $banner = @"

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   🌡️  WBGT HEAT STROKE WARNING KIOSK  🌡️                  ║
║                                                                              ║
║                           PowerShell Edition v1.0.0                         ║
║                                                                              ║
║                          Started: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Show-LocationHeader {
    param(
        [hashtable]$Location
    )
    
    $header = @"

═══════════════════════════════════════════════════════════════════════════════
                            📍 $($Location.CITY_NAME.ToUpper()) ($($Location.PREFECTURE_NAME))
═══════════════════════════════════════════════════════════════════════════════

"@
    Write-Host $header -ForegroundColor $Config.COLORS.HEADER
}

function Show-WeatherInfo {
    param(
        [hashtable]$WeatherData
    )
    
    if (-not $WeatherData) {
        Write-Host "❌ Weather data not available" -ForegroundColor Red
        return
    }
    
    Write-Host "🌤️  WEATHER INFORMATION" -ForegroundColor White
    Write-Host "   Temperature:     " -NoNewline -ForegroundColor Gray
    Write-Host "$($WeatherData.temperature)°C" -ForegroundColor $Config.COLORS.TEMPERATURE
    Write-Host "   Humidity:        " -NoNewline -ForegroundColor Gray
    Write-Host "$($WeatherData.humidity)%" -ForegroundColor $Config.COLORS.HUMIDITY
    Write-Host "   Feels Like:      " -NoNewline -ForegroundColor Gray
    Write-Host "$($WeatherData.feels_like)°C" -ForegroundColor $Config.COLORS.TEMPERATURE
    Write-Host "   Condition:       " -NoNewline -ForegroundColor Gray
    Write-Host "$($WeatherData.weather_condition)" -ForegroundColor White
    Write-Host "   Data Source:     " -NoNewline -ForegroundColor Gray
    Write-Host "$($WeatherData.source)" -ForegroundColor $Config.COLORS.INFO
    Write-Host ""
}

function Show-WBGTInfo {
    param(
        [hashtable]$WBGTData,
        [hashtable]$WeatherData
    )
    
    $wbgtValue = $null
    $wbgtLevel = $null
    $dataSource = "Not Available"
    
    if ($WBGTData) {
        $wbgtValue = $WBGTData.wbgt
        $wbgtLevel = Get-WBGTLevel -WBGTValue $wbgtValue
        $dataSource = $WBGTData.source
    } elseif ($WeatherData) {
        # Calculate WBGT from weather data
        $wbgtValue = Calculate-WBGT -Temperature $WeatherData.temperature -Humidity $WeatherData.humidity
        $wbgtLevel = Get-WBGTLevel -WBGTValue $wbgtValue
        $dataSource = "Calculated from Weather Data"
    }
    
    Write-Host "🌡️  WBGT INDEX INFORMATION" -ForegroundColor White
    
    if ($wbgtValue) {
        Write-Host "   WBGT Value:      " -NoNewline -ForegroundColor Gray
        Write-Host "$wbgtValue°C" -ForegroundColor $Config.COLORS.WBGT
        Write-Host "   Warning Level:   " -NoNewline -ForegroundColor Gray
        Write-Host "$($wbgtLevel.LEVEL)" -ForegroundColor $wbgtLevel.COLOR
        Write-Host "   Advice:          " -NoNewline -ForegroundColor Gray
        Write-Host "$($wbgtLevel.ADVICE)" -ForegroundColor Cyan
        Write-Host "   Data Source:     " -NoNewline -ForegroundColor Gray
        Write-Host "$dataSource" -ForegroundColor $Config.COLORS.INFO
    } else {
        Write-Host "   ❌ WBGT data not available" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Show-AlertInfo {
    param(
        [hashtable]$AlertData
    )
    
    if (-not $AlertData) {
        Write-Host "❌ Alert data not available" -ForegroundColor Red
        return
    }
    
    Write-Host "🚨 HEAT STROKE ALERTS" -ForegroundColor White
    
    $todayLevel = Get-AlertLevelDescription -AlertValue $AlertData.today
    $tomorrowLevel = Get-AlertLevelDescription -AlertValue $AlertData.tomorrow
    
    Write-Host "   Today:           " -NoNewline -ForegroundColor Gray
    Write-Host "$($todayLevel.level)" -ForegroundColor $todayLevel.color
    Write-Host "   Tomorrow:        " -NoNewline -ForegroundColor Gray
    Write-Host "$($tomorrowLevel.level)" -ForegroundColor $tomorrowLevel.color
    Write-Host "   Data Source:     " -NoNewline -ForegroundColor Gray
    Write-Host "$($AlertData.source)" -ForegroundColor $Config.COLORS.INFO
    
    if ($AlertData.today -eq 1) {
        Write-Host ""
        Write-Host "   ⚠️  TODAY'S ALERT ADVICE:" -ForegroundColor Red
        Write-Host "   $($todayLevel.advice)" -ForegroundColor Yellow
    }
    
    if ($AlertData.tomorrow -eq 1) {
        Write-Host ""
        Write-Host "   ⚠️  TOMORROW'S ALERT ADVICE:" -ForegroundColor Red
        Write-Host "   $($tomorrowLevel.advice)" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Show-SystemInfo {
    param(
        [int]$CycleCount,
        [datetime]$StartTime,
        [datetime]$NextUpdate
    )
    
    $uptime = (Get-Date) - $StartTime
    $uptimeString = "{0:dd}d {0:hh}h {0:mm}m {0:ss}s" -f $uptime
    
    Write-Host "📊 SYSTEM INFORMATION" -ForegroundColor White
    Write-Host "   Cycle Count:     " -NoNewline -ForegroundColor Gray
    Write-Host "$CycleCount" -ForegroundColor $Config.COLORS.INFO
    Write-Host "   Uptime:          " -NoNewline -ForegroundColor Gray
    Write-Host "$uptimeString" -ForegroundColor $Config.COLORS.INFO
    Write-Host "   Next Update:     " -NoNewline -ForegroundColor Gray
    Write-Host "$($NextUpdate.ToString("yyyy-MM-dd HH:mm:ss"))" -ForegroundColor $Config.COLORS.INFO
    Write-Host "   Service Period:  " -NoNewline -ForegroundColor Gray
    
    if (Test-ServiceAvailable) {
        Write-Host "Active (Official WBGT Available)" -ForegroundColor Green
    } else {
        Write-Host "Inactive (Using JMA API Estimation)" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

function Get-LocationData {
    param(
        [hashtable]$Location
    )
    
    $locationData = @{
        "location" = $Location
        "weather" = $null
        "wbgt" = $null
        "alert" = $null
        "errors" = @()
    }
    
    try {
        # Get weather data
        Write-Log "Fetching weather data for $($Location.CITY_NAME)" "INFO"
        $locationData.weather = Get-CurrentWeather -AreaCode $Location.AREA_CODE
        
        # Get WBGT data (try official first, then calculated)
        Write-Log "Fetching WBGT data for $($Location.CITY_NAME)" "INFO"
        if (Test-ServiceAvailable) {
            $locationData.wbgt = Get-WBGTCurrentData -PrefectureCode $Location.WBGT_CODE
        }
        
        # Get alert data
        Write-Log "Fetching alert data for $($Location.CITY_NAME)" "INFO"
        $locationData.alert = Get-AlertData -AreaCode $Location.AREA_CODE -PrefectureCode $Location.WBGT_CODE
        
    }
    catch {
        $errorMsg = "Error fetching data for $($Location.CITY_NAME): $_"
        Write-Log $errorMsg "ERROR"
        $locationData.errors += $errorMsg
    }
    
    return $locationData
}

function Show-LocationData {
    param(
        [hashtable]$LocationData
    )
    
    Show-LocationHeader -Location $LocationData.location
    Show-WeatherInfo -WeatherData $LocationData.weather
    Show-WBGTInfo -WBGTData $LocationData.wbgt -WeatherData $LocationData.weather
    Show-AlertInfo -AlertData $LocationData.alert
    
    if ($LocationData.errors.Count -gt 0) {
        Write-Host "⚠️  ERRORS ENCOUNTERED:" -ForegroundColor Red
        foreach ($error in $LocationData.errors) {
            Write-Host "   $error" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

function Update-Display {
    param(
        [array]$Locations,
        [int]$CycleCount,
        [datetime]$StartTime,
        [int]$IntervalMinutes
    )
    
    Clear-Host
    Show-Banner
    
    Write-Log "Starting display update cycle #$CycleCount" "INFO"
    
    # Calculate next update time
    $nextUpdate = (Get-Date).AddMinutes($IntervalMinutes)
    
    # Process each location
    foreach ($location in $Locations) {
        try {
            $locationData = Get-LocationData -Location $location
            Show-LocationData -LocationData $locationData
        }
        catch {
            Write-Log "Failed to process location $($location.CITY_NAME): $_" "ERROR"
            Write-Host "❌ Failed to load data for $($location.CITY_NAME)" -ForegroundColor Red
        }
    }
    
    # Show system information
    Show-SystemInfo -CycleCount $CycleCount -StartTime $StartTime -NextUpdate $nextUpdate
    
    # Show footer
    $footer = @"
═══════════════════════════════════════════════════════════════════════════════
                              Press Ctrl+C to exit
═══════════════════════════════════════════════════════════════════════════════

"@
    Write-Host $footer -ForegroundColor $Config.COLORS.TIMESTAMP
    
    Write-Log "Display update cycle #$CycleCount completed" "INFO"
}

function Start-KioskMode {
    param(
        [bool]$DemoMode = $false,
        [int]$MaxCycles = 0,
        [int]$IntervalMinutes = 30
    )
    
    # Set parameters for demo mode
    if ($DemoMode) {
        $MaxCycles = $Config.DEMO_CYCLES
        $IntervalSeconds = $Config.DEMO_INTERVAL_SECONDS
        Write-Log "Starting in demo mode: $MaxCycles cycles, $IntervalSeconds second intervals" "INFO"
    } else {
        $IntervalSeconds = $IntervalMinutes * 60
        Write-Log "Starting in normal mode: Update interval $IntervalMinutes minutes" "INFO"
    }
    
    # Main loop
    while ($script:IsRunning) {
        $script:CycleCount++
        
        try {
            Update-Display -Locations $Config.LOCATIONS -CycleCount $script:CycleCount -StartTime $script:StartTime -IntervalMinutes $IntervalMinutes
            
            # Check if we should stop
            if ($MaxCycles -gt 0 -and $script:CycleCount -ge $MaxCycles) {
                Write-Log "Reached maximum cycles ($MaxCycles), stopping" "INFO"
                break
            }
            
            # Wait for next update
            if ($script:IsRunning) {
                Write-Log "Waiting $IntervalSeconds seconds until next update..." "DEBUG"
                Start-Sleep -Seconds $IntervalSeconds
            }
        }
        catch {
            Write-Log "Error in main loop: $_" "ERROR"
            Write-Host "❌ An error occurred: $_" -ForegroundColor Red
            Start-Sleep -Seconds 10
        }
    }
    
    Write-Log "Kiosk mode stopped" "INFO"
}

function Stop-Script {
    Write-Log "Received stop signal, shutting down gracefully..." "INFO"
    $script:IsRunning = $false
}

# Main execution
try {
    # Handle help request
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Initialize console
    Initialize-Console
    
    # Set up signal handling
    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
        Stop-Script
    }
    
    # Handle Ctrl+C
    $null = Register-EngineEvent -SourceIdentifier "PowerShell.Exiting" -Action {
        Write-Log "Application interrupted by user" "INFO"
        Stop-Script
    }
    
    # Determine run parameters
    $runDemoMode = $Demo
    $runMaxCycles = if ($Cycles -gt 0) { $Cycles } else { 0 }
    $runIntervalMinutes = if ($IntervalMinutes -gt 0) { $IntervalMinutes } else { $Config.UPDATE_INTERVAL_MINUTES }
    
    # Start the kiosk
    Write-Log "WBGT Kiosk PowerShell Edition starting..." "INFO"
    Start-KioskMode -DemoMode $runDemoMode -MaxCycles $runMaxCycles -IntervalMinutes $runIntervalMinutes
    
    Write-Log "WBGT Kiosk PowerShell Edition stopped" "INFO"
    Write-Host ""
    Write-Host "Thank you for using WBGT Kiosk PowerShell Edition!" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Log "Fatal error: $_" "ERROR"
    Write-Host "❌ Fatal error occurred: $_" -ForegroundColor Red
    Write-Host "Check the log file for more details: $($Config.LOG_FILE)" -ForegroundColor Yellow
    exit 1
}
finally {
    # Clean up
    Get-EventSubscriber | Unregister-Event
}