Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$EnvFile = Join-Path $Root ".env"
$Venv = Join-Path $Root ".venv"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$Requirements = Join-Path $Root "requirements.txt"

function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return
    }
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($name -and -not [Environment]::GetEnvironmentVariable($name, "Process")) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found. Install Python 3.10+ and run this script again."
    exit 1
}

Import-DotEnv -Path $EnvFile

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating local virtual environment: .venv"
    python -m venv $Venv
}

Write-Host "Installing project dependencies..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r $Requirements

$provider = if ($env:LLM_PROVIDER) { $env:LLM_PROVIDER } else { "kimi" }
$port = if ($env:APP_PORT) { [int]$env:APP_PORT } else { 8080 }
$hostName = if ($env:APP_HOST) { $env:APP_HOST } else { "127.0.0.1" }
$keyConfigured = -not [string]::IsNullOrWhiteSpace($env:LLM_API_KEY) -or -not [string]::IsNullOrWhiteSpace($env:KIMI_API_KEY) -or $provider -eq "ollama"

try {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
} catch {
    $listener = $null
}
if ($listener) {
    Write-Host "Port $port is already in use. Change APP_PORT in .env or stop the other service."
    exit 1
}

if ($keyConfigured) {
    Write-Host "LLM provider configured: $provider"
} else {
    Write-Host "LLM key is not configured. The app will start in local mode."
    Write-Host 'Open the web app and use "Configure Model", or set LLM_API_KEY in .env.'
}

Write-Host "Starting AI-From-Zero..."
Write-Host "Local URL: http://127.0.0.1:$port"
if ($hostName -eq "0.0.0.0") {
    Write-Host "LAN mode is enabled. Use this only on trusted networks."
}

& $VenvPython (Join-Path $Backend "server.py")
