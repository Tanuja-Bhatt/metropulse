$ErrorActionPreference = "Stop"

Write-Host "=============================================="
Write-Host "METROPULSE - REPRODUCIBLE REBUILD"
Write-Host "=============================================="

Write-Host ""
Write-Host "[1/5] Download / validate taxi data"
python scripts\download_taxi.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Taxi data step failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[2/5] Download / validate weather data"
python scripts\download_weather.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Weather data step failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[3/5] Download / validate subway data"
python scripts\download_subway.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Subway data step failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[4/5] Download / validate taxi zones"
python scripts\download_zones.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Taxi zones step failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[5/5] Build DuckDB warehouse"
python scripts\build_warehouse.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warehouse build step failed."
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=============================================="
Write-Host "METRO PULSE REBUILD COMPLETE"
Write-Host "=============================================="