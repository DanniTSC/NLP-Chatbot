$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$env:DEBUG = "false"
$env:PYTHONPATH = $projectRoot
$env:CHATBOT_DEBUG_SITE = "1"

.\venv\Scripts\python.exe -m chainlit run --host 127.0.0.1 --port 8000 --headless app.py
