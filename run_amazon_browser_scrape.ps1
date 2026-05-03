param(
    [ValidateSet(1,2,3)]
    [int]$Batch = 1,

    # Pass -Resume to skip SKUs already in the JSON (useful if Chrome crashed mid-run).
    # By default every run re-scrapes all SKUs so prices are always fresh.
    [switch]$Resume
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile   = Join-Path $scriptDir '.env.production'

$python = Join-Path $scriptDir 'Thrifthammer\venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = Join-Path $scriptDir 'venv\Scripts\python.exe' }
if (-not (Test-Path $python)) {
    Write-Host 'ERROR: No venv found.' -ForegroundColor Red; pause; exit 1
}
$pip = Join-Path (Split-Path $python) 'pip.exe'

# Load production DB credentials so the scraper can query Amazon URLs from the DB
if (-not (Test-Path $envFile)) {
    Write-Host 'ERROR: .env.production not found.' -ForegroundColor Red; pause; exit 1
}
foreach ($line in Get-Content $envFile) {
    $line = $line.Trim()
    if ($line -match '^DATABASE_URL=(.+)$')      { $env:DATABASE_URL         = $Matches[1].Trim() }
    if ($line -match '^DJANGO_SECRET_KEY=(.+)$') { $env:DJANGO_SECRET_KEY    = $Matches[1].Trim() }
}
$env:RAILWAY_ENVIRONMENT  = 'production'
$env:DJANGO_ALLOWED_HOSTS = 'thrifthammer.com,www.thrifthammer.com,web-production-b6056.up.railway.app'
$env:DJANGO_DEBUG         = 'False'

Write-Host ''
Write-Host "ThriftHammer - Amazon Browser Scraper (Batch $Batch)" -ForegroundColor Cyan
Write-Host '------------------------------------------------------'
Write-Host "Using Python: $python"
Write-Host ''

Write-Host '[1/2] Ensuring playwright is installed...' -ForegroundColor Yellow
& $pip install playwright
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: pip install playwright failed.' -ForegroundColor Red; pause; exit 1
}

Write-Host ''
Write-Host '[2/2] Starting browser scraper...' -ForegroundColor Yellow
Write-Host 'Chrome will open and visit each page. Do NOT close it.' -ForegroundColor Yellow
Write-Host ''

& $python (Join-Path $scriptDir 'scrape_amazon_browser.py') --batch $Batch @(if ($Resume) { '--resume' })

if ($LASTEXITCODE -ne 0) {
    Write-Host 'Scraper exited with an error.' -ForegroundColor Red; pause; exit 1
}

Write-Host ''
Write-Host "Batch $Batch complete. Results in amazon_prices_batch${Batch}.json" -ForegroundColor Green
Write-Host "Run import_amazon_prices_batch${Batch}.ps1 to write to the database." -ForegroundColor Cyan
Write-Host ''
pause
