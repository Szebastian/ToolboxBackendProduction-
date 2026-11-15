Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "     INICIANDO TOOLBOX BACKEND (PYTHON FASTAPI)     " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Creando archivo .env desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual de Python..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activando entorno virtual..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

Write-Host "Instalando dependencias desde requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "`nServidor disponible en: http://localhost:10000" -ForegroundColor Cyan
Write-Host "Swagger Docs en:       http://localhost:10000/docs`n" -ForegroundColor Cyan

uvicorn src.main:app --reload --port 10000 --host 0.0.0.0

