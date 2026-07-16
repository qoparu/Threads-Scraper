# auto_update.ps1 — один цикл авто-обновления дашборда акимата.
# Парс Threads → очистка(Meta+Threads) → AI-фильтр Groq → сборка → деплой на Vercel.
# Запускается планировщиком Windows каждые 30–60 минут (см. register_autoupdate.ps1).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# лог с таймстампом
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$log = Join-Path $logDir ("update_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
function Say($m) { "$([DateTime]::Now.ToString('HH:mm:ss')) $m" | Tee-Object -FilePath $log -Append }

# загрузить переменные из .env
Get-Content (Join-Path $root ".env") | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim())
  }
}

$py = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# для быстрых авто-циклов берём меньше постов Threads (можно переопределить в .env)
if (-not $env:THREADS_TARGET) { $env:THREADS_TARGET = "400" }

try {
  Say "▶ 1/4 Парс Threads (цель $($env:THREADS_TARGET))…"
  & $py almaty_monitor.py *>> $log

  Say "▶ 2/4 Очистка + 3/4 AI-фильтр Groq + сборка…"
  & $py run_pipeline.py --grok *>> $log

  Say "▶ 4/4 Деплой на Vercel…"
  Set-Location (Join-Path $root "public")
  npx --yes vercel@latest deploy --prod --yes --scope $env:VERCEL_SCOPE --token $env:VERCEL_TOKEN *>> $log

  Say "✓ Цикл завершён."
}
catch {
  Say "✖ Ошибка: $_"
  exit 1
}
