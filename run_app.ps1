$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$env:DEBUG = "false"
$env:PYTHONPATH = $projectRoot
$env:CHATBOT_DEBUG_SITE = "1"
if (-not $env:USE_LOCAL_GPT) {
    $env:USE_LOCAL_GPT = "true"
}
if (-not $env:OLLAMA_MODEL) {
    $env:OLLAMA_MODEL = "llama3.2:3b"
}
if (-not $env:OLLAMA_BASE_URL) {
    $env:OLLAMA_BASE_URL = "http://localhost:11434"
}
if (-not $env:OLLAMA_TIMEOUT_SECONDS) {
    $env:OLLAMA_TIMEOUT_SECONDS = "20"
}

if ($env:USE_LOCAL_GPT -eq "true") {
    try {
        Invoke-RestMethod -Uri "$($env:OLLAMA_BASE_URL)/api/tags" -TimeoutSec 2 | Out-Null
        Write-Host "Ollama is reachable at $($env:OLLAMA_BASE_URL), model=$($env:OLLAMA_MODEL)"
    }
    catch {
        Write-Warning "Ollama is not reachable. The app will still run with template fallback responses."
    }
}

.\venv\Scripts\python.exe -m chainlit run --host 127.0.0.1 --port 8000 --headless app.py
