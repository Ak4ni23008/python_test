# CloudTrade — start all 3 processes (open 3 separate terminals if this fails)
$root = $PSScriptRoot

Write-Host "=== CloudTrade local run ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open 3 PowerShell windows and run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1) API:" -ForegroundColor Green
Write-Host "   cd `"$root\backend`""
Write-Host "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "2) Worker:" -ForegroundColor Green
Write-Host "   cd `"$root\backend`""
Write-Host "   python -m app.workers.live_worker"
Write-Host ""
Write-Host "3) Frontend:" -ForegroundColor Green
Write-Host "   cd `"$root\frontend`""
Write-Host "   npm install"
Write-Host "   npm run dev"
Write-Host ""
Write-Host "Then open: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API health: http://localhost:8000/health" -ForegroundColor Cyan
