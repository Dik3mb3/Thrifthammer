param(
    [ValidateSet(1,2,3,0)]
    [int]$Batch = 0,

    # Scrape all products with a specific batch_tag (e.g. -BatchTag blood-bowl).
    # When set, --batch is ignored.
    [string]$BatchTag = '',

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

if (-not $BatchTag -and $Batch -eq 0) {
    Write-Host 'ERROR: Provide -Batch (1/2/3) or -BatchTag <tag> (e.g. -BatchTag blood-bowl).' -ForegroundColor Red
    pause; exit 1
}

$label = if ($BatchTag) { "BatchTag=$BatchTag" } else { "Batch $Batch" }

Write-Host ''
Write-Host "ThriftHammer - Amazon Browser Scraper ($label)" -ForegroundColor Cyan
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

$scriptArgs = @()
if ($BatchTag) {
    $scriptArgs += '--batch-tag', $BatchTag
} else {
    $scriptArgs += '--batch', $Batch
}
if ($Resume) { $scriptArgs += '--resume' }

& $python (Join-Path $scriptDir 'scrape_amazon_browser.py') @scriptArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host 'Scraper exited with an error.' -ForegroundColor Red; pause; exit 1
}

$outFile = if ($BatchTag) { "amazon_prices_tag_$($BatchTag.Replace('-','_')).json" } else { "amazon_prices_batch${Batch}.json" }
Write-Host ''
Write-Host "$label complete. Results in $outFile" -ForegroundColor Green
Write-Host ''
pause
