# WBGT熱中症警戒キオスク Windows サービス インストール スクリプト
# 管理者権限で実行する必要があります

param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = (Get-Location).Path,
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "WBGTKiosk",
    
    [Parameter(Mandatory=$false)]
    [string]$DisplayName = "WBGT熱中症警戒キオスク"
)

# 管理者権限チェック
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ このスクリプトは管理者権限で実行する必要があります。" -ForegroundColor Red
    Write-Host "PowerShellを右クリックして「管理者として実行」を選択してください。" -ForegroundColor Yellow
    exit 1
}

Write-Host "🌡️  WBGT熱中症警戒キオスク Windows サービス インストール  🌡️" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Pythonの確認
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    $pythonVersion = python --version
    Write-Host "✅ Python確認: $pythonVersion ($pythonPath)" -ForegroundColor Green
} catch {
    Write-Host "❌ Pythonが見つかりません。Pythonをインストールしてください。" -ForegroundColor Red
    Write-Host "Python公式サイト: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# NSSMの確認とインストール
$nssmPath = "$InstallPath\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "ℹ️  NSSM (Non-Sucking Service Manager) をダウンロード中..." -ForegroundColor Blue
    
    try {
        # NSSMの最新版をダウンロード
        $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
        $nssmZip = "$InstallPath\nssm.zip"
        
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        
        # 解凍
        Expand-Archive -Path $nssmZip -DestinationPath $InstallPath -Force
        
        # 実行ファイルをコピー
        $nssmExe = "$InstallPath\nssm-2.24\win64\nssm.exe"
        if (Test-Path $nssmExe) {
            Copy-Item $nssmExe $nssmPath
        } else {
            $nssmExe = "$InstallPath\nssm-2.24\win32\nssm.exe"
            Copy-Item $nssmExe $nssmPath
        }
        
        # 一時ファイルを削除
        Remove-Item $nssmZip -Force
        Remove-Item "$InstallPath\nssm-2.24" -Recurse -Force
        
        Write-Host "✅ NSSM のダウンロードと設定が完了しました。" -ForegroundColor Green
    } catch {
        Write-Host "❌ NSSM のダウンロードに失敗しました: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# 既存サービスの確認と停止
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "⚠️  既存のサービス '$ServiceName' が見つかりました。停止して削除します。" -ForegroundColor Yellow
    
    if ($existingService.Status -eq 'Running') {
        Stop-Service -Name $ServiceName -Force
        Write-Host "🛑 サービスを停止しました。" -ForegroundColor Yellow
    }
    
    & $nssmPath remove $ServiceName confirm
    Write-Host "🗑️  既存のサービスを削除しました。" -ForegroundColor Yellow
}

# サービスの作成
Write-Host "ℹ️  サービス '$ServiceName' を作成中..." -ForegroundColor Blue

# サービスの基本設定
& $nssmPath install $ServiceName $pythonPath "$InstallPath\src\wbgt_kiosk.py"
& $nssmPath set $ServiceName DisplayName $DisplayName
& $nssmPath set $ServiceName Description "WBGT熱中症警戒情報を表示するキオスクサービス"
& $nssmPath set $ServiceName Start SERVICE_AUTO_START
& $nssmPath set $ServiceName AppDirectory $InstallPath

# ログ設定
$logPath = "$InstallPath\service.log"
& $nssmPath set $ServiceName AppStdout $logPath
& $nssmPath set $ServiceName AppStderr $logPath

# 環境変数設定
& $nssmPath set $ServiceName AppEnvironmentExtra "PYTHONUNBUFFERED=1"

# 失敗時の再起動設定
& $nssmPath set $ServiceName AppRestartDelay 10000

Write-Host "✅ サービスの作成が完了しました。" -ForegroundColor Green

# サービスの開始
Write-Host "ℹ️  サービスを開始中..." -ForegroundColor Blue
try {
    Start-Service -Name $ServiceName
    Write-Host "✅ サービス '$ServiceName' が正常に開始されました。" -ForegroundColor Green
} catch {
    Write-Host "⚠️  サービスの開始に失敗しました: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "手動でサービスを開始してください: services.msc" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🎉 Windows サービスのインストールが完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 サービス情報:" -ForegroundColor White
Write-Host "  サービス名: $ServiceName" -ForegroundColor White
Write-Host "  表示名: $DisplayName" -ForegroundColor White
Write-Host "  インストールパス: $InstallPath" -ForegroundColor White
Write-Host "  ログファイル: $logPath" -ForegroundColor White
Write-Host ""
Write-Host "🔧 サービス管理:" -ForegroundColor White
Write-Host "  サービス開始: Start-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  サービス停止: Stop-Service -Name $ServiceName" -ForegroundColor White
Write-Host "  サービス削除: $nssmPath remove $ServiceName confirm" -ForegroundColor White
Write-Host "  サービス管理画面: services.msc" -ForegroundColor White
Write-Host ""
Write-Host "📊 ログ確認:" -ForegroundColor White
Write-Host "  Get-Content $logPath -Tail 20" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan