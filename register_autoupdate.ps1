# register_autoupdate.ps1 — регистрирует задачу Windows, которая обновляет дашборд
# каждые 45 минут (вызывает auto_update.ps1). Запусти ОДИН раз:
#     powershell -ExecutionPolicy Bypass -File register_autoupdate.ps1
#
# Управление после регистрации:
#   Get-ScheduledTask AlmatyDashboardUpdate              # статус
#   Start-ScheduledTask AlmatyDashboardUpdate            # запустить сейчас
#   Unregister-ScheduledTask AlmatyDashboardUpdate -Confirm:$false   # удалить

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $root "auto_update.ps1"
$IntervalMinutes = 45   # период обновления (30–60)

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
  -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "AlmatyDashboardUpdate" `
  -Action $action -Trigger $trigger -Settings $settings `
  -Description "Авто-обновление дашборда акимата Алматы (Threads + Meta -> Groq -> Vercel)" `
  -Force | Out-Null

Write-Host "✓ Задача 'AlmatyDashboardUpdate' зарегистрирована: каждые $IntervalMinutes мин." -ForegroundColor Green
Write-Host "  Первый запуск — через 1 минуту. Логи: $root\logs\"
Write-Host "  Удалить: Unregister-ScheduledTask AlmatyDashboardUpdate -Confirm:`$false"
