# WBGT熱中症警戒キオスク Windows サービス アンインストール スクリプト
# 管理者権限で実行する必要があります

param(
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "WBGTKiosk"
)

# 管理者権限チェック
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ このスクリプトは管理者権限で実行する必要があります。" -ForegroundColor Red
    Write-Host "PowerShellを右クリックして「管理者として実行」を選択してください。" -ForegroundColor Yellow
    exit 1
}

Write-Host "🌡️  WBGT熱中症警戒キオスク Windows サービス アンインストール  🌡️" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

# NSSMの確認
$nssmPath = ".\nssm.exe"
if (-not (Test-Path $nssmPath)) {
    Write-Host "❌ NSSM (nssm.exe) が見つかりません。" -ForegroundColor Red
    Write-Host "インストール時に作成されたnssm.exeが同じフォルダにあることを確認してください。" -ForegroundColor Yellow
    exit 1
}

# サービスの確認
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $existingService) {
    Write-Host "ℹ️  サービス '$ServiceName' は見つかりませんでした。" -ForegroundColor Blue
    Write-Host "既にアンインストール済みか、サービス名が異なる可能性があります。" -ForegroundColor Yellow
    exit 0
}

# サービスの停止
Write-Host "ℹ️  サービス '$ServiceName' を停止中..." -ForegroundColor Blue
if ($existingService.Status -eq 'Running') {
    try {
        Stop-Service -Name $ServiceName -Force
        Write-Host "✅ サービスを停止しました。" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  サービスの停止に失敗しました: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "ℹ️  サービスは既に停止しています。" -ForegroundColor Blue
}

# サービスの削除
Write-Host "ℹ️  サービス '$ServiceName' を削除中..." -ForegroundColor Blue
try {
    & $nssmPath remove $ServiceName confirm
    Write-Host "✅ サービスを削除しました。" -ForegroundColor Green
} catch {
    Write-Host "❌ サービスの削除に失敗しました: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "🎉 Windows サービスのアンインストールが完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 完了した作業:" -ForegroundColor White
Write-Host "  ✅ サービス '$ServiceName' の停止" -ForegroundColor White
Write-Host "  ✅ サービス '$ServiceName' の削除" -ForegroundColor White
Write-Host ""
Write-Host "🗑️  手動で削除が必要なファイル（必要に応じて）:" -ForegroundColor White
Write-Host "  - nssm.exe" -ForegroundColor White
Write-Host "  - service.log" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan