Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$EnvFile = Join-Path $Root ".env"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found. Please install Python 3.10+ and try again."
    exit 1
}

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            if (-not [Environment]::GetEnvironmentVariable($parts[0], "Process")) {
                [Environment]::SetEnvironmentVariable($parts[0], $parts[1].Trim('"').Trim("'"), "Process")
            }
        }
    }
}

$provider = if ($env:LLM_PROVIDER) { $env:LLM_PROVIDER } else { "kimi" }
$keyConfigured = -not [string]::IsNullOrWhiteSpace($env:LLM_API_KEY) -or -not [string]::IsNullOrWhiteSpace($env:KIMI_API_KEY) -or $provider -eq "ollama"
if (-not $keyConfigured) {
    Write-Host "LLM_API_KEY is not set. The app will still run with local term matching."
    Write-Host 'To enable full LLM analysis, open the app and click "配置模型", or set $env:LLM_API_KEY="your_key_here"'
} else {
    Write-Host "LLM provider '$provider' is configured. Full LLM analysis is enabled."
}

Push-Location $Backend
try {
    python -m pip install -r requirements.txt
    $port = if ($env:APP_PORT) { $env:APP_PORT } else { "8080" }
    Write-Host "Starting AI-From-Zero at http://localhost:$port"
    python server.py
}
finally {
    Pop-Location
}
