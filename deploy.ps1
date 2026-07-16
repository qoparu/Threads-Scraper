# deploy.ps1 - publish the static dashboard from public/ to Vercel.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File deploy.ps1
#
# Optional .env values:
#   VERCEL_TOKEN=...
#   VERCEL_SCOPE=...

$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$pub = Join-Path $root "public"
$envFile = Join-Path $root ".env"

if (-not (Test-Path (Join-Path $pub "index.html"))) {
  Write-Error "Missing public/index.html. Run: python build_dashboard.py"
}

if (Test-Path $envFile) {
  Get-Content -Encoding UTF8 $envFile | ForEach-Object {
    if ($_ -match "^\s*#" -or $_ -notmatch "=") { return }
    $parts = $_ -split "=", 2
    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($name -eq "VERCEL_TOKEN" -and -not $env:VERCEL_TOKEN) { $env:VERCEL_TOKEN = $value }
    if ($name -eq "VERCEL_SCOPE" -and -not $env:VERCEL_SCOPE) { $env:VERCEL_SCOPE = $value }
  }
}

$args = @("--yes", "vercel@latest", "deploy", "--prod", "--public", "--yes")
if ($env:VERCEL_TOKEN) { $args += @("--token", $env:VERCEL_TOKEN) }
if ($env:VERCEL_SCOPE) { $args += @("--scope", $env:VERCEL_SCOPE) }

Push-Location $pub
try {
  Write-Host "Deploying dashboard to Vercel production..."
  & npx.cmd @args
}
finally {
  Pop-Location
}
