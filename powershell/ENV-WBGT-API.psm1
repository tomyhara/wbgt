# Environment Ministry WBGT API Client Module
# PowerShell Version - English

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

function Test-ServiceAvailable {
    # Environment Ministry WBGT service is available from April 23 to October 22
    $currentDate = Get-Date
    $currentYear = $currentDate.Year
    
    $startDate = Get-Date -Year $currentYear -Month 4 -Day 23
    $endDate = Get-Date -Year $currentYear -Month 10 -Day 22
    
    if ($currentDate -ge $startDate -and $currentDate -le $endDate) {
        return $true
    }
    
    # Check if we're in the next year's service period
    $nextYearStart = Get-Date -Year ($currentYear + 1) -Month 4 -Day 23
    if ($currentDate -lt $startDate) {
        # We're before this year's service period, check last year
        $lastYearEnd = Get-Date -Year ($currentYear - 1) -Month 10 -Day 22
        return $currentDate -le $lastYearEnd
    }
    
    return $false
}

function Get-WBGTForecastData {
    param(
        [string]$PrefectureCode,
        [string]$Date = $null
    )
    
    if (-not (Test-ServiceAvailable)) {
        Write-Log "Environment Ministry WBGT service is not available (service period: April 23 - October 22)" "WARNING"
        return $null
    }
    
    try {
        if (-not $Date) {
            $Date = (Get-Date).ToString("yyyy-MM-dd")
        }
        
        $url = "$($Config.ENV_WBGT_BASE_URL)?prefecture_no=$PrefectureCode&date_str=$Date"
        Write-Log "Fetching WBGT forecast data from: $url" "DEBUG"
        
        $headers = @{
            "User-Agent" = $Config.USER_AGENT
            "Accept" = "text/csv"
        }
        
        $response = Invoke-WebRequest -Uri $url -Method Get -Headers $headers -TimeoutSec $Config.REQUEST_TIMEOUT
        
        if (-not $response -or $response.StatusCode -ne 200) {
            throw "Failed to fetch WBGT forecast data: HTTP $($response.StatusCode)"
        }
        
        $csvData = $response.Content
        if (-not $csvData -or $csvData.Length -lt 10) {
            Write-Log "No WBGT forecast data available for prefecture $PrefectureCode" "WARNING"
            return $null
        }
        
        # Parse CSV data
        $lines = $csvData -split "`n"
        $result = @()
        
        foreach ($line in $lines) {
            if (-not $line.Trim() -or $line.StartsWith("#")) {
                continue
            }
            
            $columns = $line -split ","
            if ($columns.Count -ge 3) {
                $entry = @{
                    "time" = $columns[0].Trim()
                    "wbgt" = $null
                    "temperature" = $null
                    "humidity" = $null
                }
                
                # Try to parse WBGT value
                if ($columns[1].Trim() -and $columns[1].Trim() -ne "-" -and $columns[1].Trim() -ne "null") {
                    try {
                        $entry.wbgt = [double]$columns[1].Trim()
                    }
                    catch {
                        Write-Log "Failed to parse WBGT value: $($columns[1])" "DEBUG"
                    }
                }
                
                # Try to parse temperature if available
                if ($columns.Count -ge 4 -and $columns[2].Trim() -and $columns[2].Trim() -ne "-" -and $columns[2].Trim() -ne "null") {
                    try {
                        $entry.temperature = [double]$columns[2].Trim()
                    }
                    catch {
                        Write-Log "Failed to parse temperature value: $($columns[2])" "DEBUG"
                    }
                }
                
                # Try to parse humidity if available
                if ($columns.Count -ge 5 -and $columns[3].Trim() -and $columns[3].Trim() -ne "-" -and $columns[3].Trim() -ne "null") {
                    try {
                        $entry.humidity = [double]$columns[3].Trim()
                    }
                    catch {
                        Write-Log "Failed to parse humidity value: $($columns[3])" "DEBUG"
                    }
                }
                
                $result += $entry
            }
        }
        
        if ($result.Count -eq 0) {
            Write-Log "No valid WBGT forecast data found for prefecture $PrefectureCode" "WARNING"
            return $null
        }
        
        Write-Log "Successfully retrieved $($result.Count) WBGT forecast entries for prefecture $PrefectureCode" "INFO"
        return $result
    }
    catch {
        Write-Log "Error fetching WBGT forecast data: $_" "ERROR"
        return $null
    }
}

function Get-WBGTCurrentData {
    param(
        [string]$PrefectureCode
    )
    
    if (-not (Test-ServiceAvailable)) {
        Write-Log "Environment Ministry WBGT service is not available (service period: April 23 - October 22)" "WARNING"
        return $null
    }
    
    try {
        $currentDate = (Get-Date).ToString("yyyy-MM-dd")
        $forecastData = Get-WBGTForecastData -PrefectureCode $PrefectureCode -Date $currentDate
        
        if (-not $forecastData -or $forecastData.Count -eq 0) {
            return $null
        }
        
        # Find the most recent data point
        $currentHour = (Get-Date).Hour
        $currentData = $null
        
        foreach ($entry in $forecastData) {
            if ($entry.time -match "(\d{1,2}):00" -and $entry.wbgt -ne $null) {
                $entryHour = [int]$matches[1]
                if ($entryHour -le $currentHour) {
                    $currentData = $entry
                } else {
                    break
                }
            }
        }
        
        if (-not $currentData) {
            # If no past data, get the first available data
            $currentData = $forecastData | Where-Object { $_.wbgt -ne $null } | Select-Object -First 1
        }
        
        if ($currentData) {
            $result = @{
                "wbgt" = $currentData.wbgt
                "temperature" = $currentData.temperature
                "humidity" = $currentData.humidity
                "time" = $currentData.time
                "source" = "Environment Ministry (Official)"
                "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            }
            
            Write-Log "Current WBGT data retrieved: WBGT=$($result.wbgt)°C" "INFO"
            return $result
        }
        
        return $null
    }
    catch {
        Write-Log "Error fetching current WBGT data: $_" "ERROR"
        return $null
    }
}

function Get-AlertData {
    param(
        [string]$PrefectureCode,
        [string]$Date = $null
    )
    
    if (-not (Test-ServiceAvailable)) {
        Write-Log "Environment Ministry WBGT service is not available (service period: April 23 - October 22)" "WARNING"
        return $null
    }
    
    try {
        if (-not $Date) {
            $Date = (Get-Date).ToString("yyyy-MM-dd")
        }
        
        $url = "$($Config.ENV_ALERT_BASE_URL)?prefecture_no=$PrefectureCode&date_str=$Date"
        Write-Log "Fetching alert data from: $url" "DEBUG"
        
        $headers = @{
            "User-Agent" = $Config.USER_AGENT
            "Accept" = "text/csv"
        }
        
        $response = Invoke-WebRequest -Uri $url -Method Get -Headers $headers -TimeoutSec $Config.REQUEST_TIMEOUT
        
        if (-not $response -or $response.StatusCode -ne 200) {
            throw "Failed to fetch alert data: HTTP $($response.StatusCode)"
        }
        
        $csvData = $response.Content
        if (-not $csvData -or $csvData.Length -lt 10) {
            Write-Log "No alert data available for prefecture $PrefectureCode" "WARNING"
            return $null
        }
        
        # Parse CSV data
        $lines = $csvData -split "`n"
        $result = @{
            "today" = 0
            "tomorrow" = 0
            "prefecture_code" = $PrefectureCode
            "date" = $Date
            "source" = "Environment Ministry (Official)"
            "timestamp" = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        }
        
        foreach ($line in $lines) {
            if (-not $line.Trim() -or $line.StartsWith("#")) {
                continue
            }
            
            $columns = $line -split ","
            if ($columns.Count -ge 2) {
                $dateStr = $columns[0].Trim()
                $alertLevel = $columns[1].Trim()
                
                # Parse alert level
                $level = 0
                if ($alertLevel -eq "1" -or $alertLevel -eq "true" -or $alertLevel -eq "alert") {
                    $level = 1
                }
                
                # Determine if it's today or tomorrow
                $today = Get-Date -Format "yyyy-MM-dd"
                $tomorrow = (Get-Date).AddDays(1).ToString("yyyy-MM-dd")
                
                if ($dateStr -eq $today) {
                    $result.today = $level
                } elseif ($dateStr -eq $tomorrow) {
                    $result.tomorrow = $level
                }
            }
        }
        
        Write-Log "Alert data retrieved: Today=$($result.today), Tomorrow=$($result.tomorrow)" "INFO"
        return $result
    }
    catch {
        Write-Log "Error fetching alert data: $_" "ERROR"
        return $null
    }
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

function Get-AlertLevel {
    param(
        [int]$AlertValue
    )
    
    if ($Config.ALERT_LEVELS.ContainsKey($AlertValue)) {
        return $Config.ALERT_LEVELS[$AlertValue]
    }
    
    return $Config.ALERT_LEVELS[0]  # Default to no alert
}

function Get-PrefectureNameFromCode {
    param(
        [string]$PrefectureCode
    )
    
    foreach ($mapping in $Config.PREFECTURE_MAPPING.GetEnumerator()) {
        if ($mapping.Value -eq $PrefectureCode) {
            return $mapping.Key
        }
    }
    
    return "Unknown"
}

# Export functions
Export-ModuleMember -Function Get-WBGTForecastData, Get-WBGTCurrentData, Get-AlertData, Test-ServiceAvailable, Get-WBGTLevel, Get-AlertLevel, Get-PrefectureNameFromCode