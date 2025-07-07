# WBGT Kiosk Launcher Script
# PowerShell Version - English

param(
    [switch]$Demo,
    [switch]$Help,
    [int]$Cycles = 0,
    [int]$IntervalMinutes = 0
)

# Get script directory
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Function to show help
function Show-LauncherHelp {
    $helpText = @"

═══════════════════════════════════════════════════════════════════════════════
                       🚀 WBGT Kiosk Launcher 🚀
═══════════════════════════════════════════════════════════════════════════════

DESCRIPTION:
    Launcher script for the WBGT Heat Stroke Warning Kiosk PowerShell Edition.
    This script provides a convenient way to start the kiosk with various options.

USAGE:
    .\run_wbgt.ps1 [OPTIONS]

OPTIONS:
    -Demo                   Run in demo mode (3 cycles, 5-second intervals)
    -Help                   Show this help message
    -Cycles <number>        Number of update cycles (0 = infinite)
    -IntervalMinutes <min>  Update interval in minutes (default: 30)

EXAMPLES:
    .\run_wbgt.ps1                           # Normal operation
    .\run_wbgt.ps1 -Demo                     # Demo mode
    .\run_wbgt.ps1 -Cycles 5                 # Run 5 cycles then exit
    .\run_wbgt.ps1 -IntervalMinutes 15       # Update every 15 minutes

SYSTEM REQUIREMENTS:
    - Windows PowerShell 5.1 or PowerShell 7+
    - Internet connection for API access
    - Execution policy allowing script execution

SETUP:
    1. Ensure PowerShell execution policy allows script execution:
       Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

    2. Edit config.ps1 to configure your preferred locations and settings

    3. Run this script to start the kiosk

TROUBLESHOOTING:
    - If you get execution policy errors, run:
      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

    - If modules fail to load, ensure all files are in the same directory

    - Check the log file (wbgt_kiosk.log) for detailed error information

═══════════════════════════════════════════════════════════════════════════════

"@
    Write-Host $helpText -ForegroundColor Cyan
}

# Function to check prerequisites
function Test-Prerequisites {
    $errors = @()
    
    # Check if main script exists
    $mainScript = Join-Path $ScriptDirectory "WBGT-Kiosk.ps1"
    if (-not (Test-Path $mainScript)) {
        $errors += "Main script not found: $mainScript"
    }
    
    # Check if config exists
    $configFile = Join-Path $ScriptDirectory "config.ps1"
    if (-not (Test-Path $configFile)) {
        $errors += "Configuration file not found: $configFile"
    }
    
    # Check if required modules exist
    $requiredModules = @("JMA-API.psm1", "ENV-WBGT-API.psm1", "HeatStroke-Alert.psm1")
    foreach ($module in $requiredModules) {
        $modulePath = Join-Path $ScriptDirectory $module
        if (-not (Test-Path $modulePath)) {
            $errors += "Required module not found: $module"
        }
    }
    
    # Check PowerShell version
    $psVersion = $PSVersionTable.PSVersion
    if ($psVersion.Major -lt 5) {
        $errors += "PowerShell version $($psVersion.Major).$($psVersion.Minor) is not supported. Please use PowerShell 5.1 or later."
    }
    
    # Check internet connectivity
    try {
        $null = Test-NetConnection -ComputerName "www.jma.go.jp" -Port 443 -InformationLevel Quiet -ErrorAction Stop
    }
    catch {
        $errors += "Internet connectivity check failed. Please ensure you have internet access."
    }
    
    return $errors
}

# Function to check execution policy
function Test-ExecutionPolicy {
    $currentPolicy = Get-ExecutionPolicy
    $restrictivePolicies = @("Restricted", "AllSigned")
    
    if ($currentPolicy -in $restrictivePolicies) {
        Write-Host "⚠️  WARNING: Current execution policy is '$currentPolicy'" -ForegroundColor Yellow
        Write-Host "This may prevent the script from running properly." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To fix this, run the following command as an administrator:" -ForegroundColor Cyan
        Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
        Write-Host ""
        Write-Host "Do you want to continue anyway? (y/N): " -NoNewline -ForegroundColor Yellow
        $response = Read-Host
        
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Host "Execution cancelled by user." -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# Main execution
try {
    # Show help if requested
    if ($Help) {
        Show-LauncherHelp
        exit 0
    }
    
    Write-Host ""
    Write-Host "🚀 WBGT Kiosk Launcher - PowerShell Edition" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Check execution policy
    Write-Host "🔍 Checking execution policy..." -ForegroundColor Yellow
    if (-not (Test-ExecutionPolicy)) {
        exit 1
    }
    
    # Check prerequisites
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow
    $prerequisiteErrors = Test-Prerequisites
    
    if ($prerequisiteErrors.Count -gt 0) {
        Write-Host "❌ Prerequisites check failed:" -ForegroundColor Red
        foreach ($error in $prerequisiteErrors) {
            Write-Host "   - $error" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "Please resolve these issues before running the kiosk." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Prerequisites check passed" -ForegroundColor Green
    Write-Host ""
    
    # Prepare parameters for main script
    $scriptParams = @{}
    
    if ($Demo) {
        $scriptParams['Demo'] = $true
        Write-Host "🎮 Starting in demo mode..." -ForegroundColor Yellow
    } else {
        Write-Host "🏃 Starting in normal mode..." -ForegroundColor Green
    }
    
    if ($Cycles -gt 0) {
        $scriptParams['Cycles'] = $Cycles
        Write-Host "🔄 Will run for $Cycles cycles" -ForegroundColor Cyan
    }
    
    if ($IntervalMinutes -gt 0) {
        $scriptParams['IntervalMinutes'] = $IntervalMinutes
        Write-Host "⏰ Update interval set to $IntervalMinutes minutes" -ForegroundColor Cyan
    }
    
    Write-Host ""
    
    # Launch main script
    $mainScript = Join-Path $ScriptDirectory "WBGT-Kiosk.ps1"
    Write-Host "🚀 Launching WBGT Kiosk..." -ForegroundColor Green
    Write-Host ""
    
    # Execute main script with parameters
    if ($scriptParams.Count -gt 0) {
        & $mainScript @scriptParams
    } else {
        & $mainScript
    }
    
}
catch {
    Write-Host ""
    Write-Host "❌ Error occurred during launch: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting suggestions:" -ForegroundColor Yellow
    Write-Host "1. Check that all files are in the same directory" -ForegroundColor Yellow
    Write-Host "2. Verify internet connection" -ForegroundColor Yellow
    Write-Host "3. Run with -Help for more information" -ForegroundColor Yellow
    Write-Host "4. Check the log file for detailed error information" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
finally {
    Write-Host ""
    Write-Host "🏁 Launcher finished" -ForegroundColor Gray
}