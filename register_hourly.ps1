# register_hourly.ps1 — register hourly Threads scraper in Windows Task Scheduler
# Run once (as Administrator):
#   powershell -ExecutionPolicy Bypass -File register_hourly.ps1

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py   = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $py) {
    Write-Error "Python not found. Set the path manually in the variable py."
    exit 1
}

$script = Join-Path $root "run_hourly.py"
$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

$action = New-ScheduledTaskAction `
    -Execute          $py `
    -Argument         "`"$script`"" `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(2) `
    -RepetitionInterval (New-TimeSpan -Hours 1)

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances  IgnoreNew `
    -DontStopOnIdleEnd

Register-ScheduledTask `
    -TaskName    "AlmatyHourlyScraper" `
    -Action      $action `
    -Trigger     $trigger `
    -Settings    $settings `
    -Description "Hourly Threads scraper (Almaty) -> output/ + logs/hourly_stats.json" `
    -Force | Out-Null

Write-Host ""
Write-Host "OK  Task 'AlmatyHourlyScraper' registered: every hour." -ForegroundColor Green
Write-Host "    First run in 2 minutes."
Write-Host "    Python : $py"
Write-Host "    Script : $script"
Write-Host "    Logs   : $logDir\hourly_*.log"
Write-Host "    Stats  : $logDir\hourly_stats.json"
Write-Host "    Data   : $root\output\hourly_*.json"
Write-Host ""
Write-Host "Management:" -ForegroundColor Cyan
Write-Host "    Start-ScheduledTask AlmatyHourlyScraper"
Write-Host "    Get-ScheduledTask   AlmatyHourlyScraper"
Write-Host "    Unregister-ScheduledTask AlmatyHourlyScraper -Confirm:`$false"
