# Fix MT5 default server stuck on MetaQuotes-Demo for XM account 101537675
# Run this with MT5 CLOSED (right-click PowerShell -> Run as normal user)

$cfg = Join-Path $env:APPDATA "MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\config"
if (-not (Test-Path $cfg)) {
    Write-Error "MT5 config folder not found. Open MT5 -> File -> Open Data Folder to find your path."
    exit 1
}

Write-Host "Stopping MetaTrader 5..."
Stop-Process -Name terminal64 -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "$cfg\common.ini" "$cfg\common.ini.bak-$stamp" -Force
Copy-Item "$cfg\accounts.dat" "$cfg\accounts.dat.bak-$stamp" -Force -ErrorAction SilentlyContinue

$content = Get-Content "$cfg\common.ini" -Raw
$content = $content -replace 'Server=MetaQuotes-Demo', 'Server=XMGlobal-MT5'
$content = $content -replace 'Account=1', 'Account=0'
$content = $content -replace 'Profile=1', 'Profile=0'
if ($content -notmatch 'Server=XMGlobal-MT5') {
    $content = $content -replace '(Login=101537675)', "`$1`r`nServer=XMGlobal-MT5"
}
Set-Content "$cfg\common.ini" $content -NoNewline

# Remove wrong account/server pairing (MT5 recreates on next login)
Remove-Item "$cfg\accounts.dat" -Force -ErrorAction SilentlyContinue

Write-Host "Done. common.ini now uses XMGlobal-MT5."
Write-Host "Starting MT5..."
Start-Process "C:\Program Files\MetaTrader 5\terminal64.exe"
Write-Host ""
Write-Host "In MT5:"
Write-Host "  1. File -> Login to Trade Account"
Write-Host "  2. Server: XMGlobal-MT5  Login: 101537675"
Write-Host "  3. Do NOT use MetaQuotes-Demo for this account"
