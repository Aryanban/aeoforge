# ==============================================================================
# AEOForge - Automated Local Setup & Launch Engine (Windows PowerShell)
# ==============================================================================
param (
    [string]$Action = "--start",
    [string]$Param1 = "8000"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  AEOForge • Automated Local Setup & Launch Engine (Windows)" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/5] Checking Python runtime..." -ForegroundColor Blue
$PyCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PyCmd = $cmd
        break
    }
}

if (-not $PyCmd) {
    Write-Error "Python 3.10 or higher is required. Please install Python from python.org."
    exit 1
}
Write-Host "✓ Found Python: $PyCmd" -ForegroundColor Green

# 2. Virtual Environment
Write-Host "`n[2/5] Initializing Python virtual environment..." -ForegroundColor Blue
if (-not (Test-Path ".venv")) {
    & $PyCmd -m venv .venv
}
Write-Host "✓ Virtual environment ready." -ForegroundColor Green

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$VenvPip = Join-Path $ScriptDir ".venv\Scripts\pip.exe"

# 3. Dependencies
Write-Host "`n[3/5] Installing dependencies..." -ForegroundColor Blue
& $VenvPip install --upgrade pip setuptools wheel --quiet
& $VenvPip install -e . --quiet
Write-Host "✓ Dependencies installed." -ForegroundColor Green

# 4. Playwright Browser
Write-Host "`n[4/5] Verifying Playwright browser..." -ForegroundColor Blue
& $VenvPython -m playwright install chromium
Write-Host "✓ Playwright Chromium browser installed." -ForegroundColor Green

# 5. Data directory
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

Write-Host "`n==============================================================================" -ForegroundColor Green
Write-Host "✨ AEOForge environment is configured and ready!" -ForegroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green

if ($Action -in @("--start", "start", "serve", "--open")) {
    $Port = if ($Param1) { $Param1 } else { "8000" }
    Write-Host "`n🚀 Launching AEOForge Web UI on http://127.0.0.1:$Port..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:$Port"
    & $VenvPython -m uvicorn aeoforge.main:app --host 127.0.0.1 --port $Port --reload
} elseif ($Action -in @("--test", "test")) {
    & $VenvPython -m pytest -v
} elseif ($Action -in @("--audit", "audit")) {
    if (-not $Param1 -or $Param1 -eq "8000") {
        Write-Error "Please specify a URL to audit. Example: .\setup.ps1 -Action audit -Param1 https://example.com"
        exit 1
    }
    & $VenvPython -m aeoforge.cli audit $Param1
} else {
    Write-Host "`nUsage:"
    Write-Host "  .\setup.ps1 -Action start"
    Write-Host "  .\setup.ps1 -Action test"
    Write-Host "  .\setup.ps1 -Action audit -Param1 https://dholeramap.com"
}
