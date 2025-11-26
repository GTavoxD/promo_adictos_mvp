# setup_and_run.ps1
# Script todo-en-uno para PromoAdictos:
# - Verifica .venv
# - Instala requirements
# - Verifica dependencias clave
# - Ejecuta el bot
# - Guarda log en .\logs\

param(
    [switch]$SoloInstalar
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   PromoAdictos - Setup y Ejecucion" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Ir a la carpeta donde está el script
Set-Location -Path $PSScriptRoot

# Rutas básicas
$venvPath  = ".venv"
$venvPy    = ".venv\Scripts\python.exe"
$venvPip   = ".venv\Scripts\pip.exe"
$logsDir   = "logs"

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# 1) Verificar que exista .venv
if (-not (Test-Path $venvPy)) {
    Write-Host "[ERROR] No se encontro el entorno virtual .venv." -ForegroundColor Red
    Write-Host "Crea uno con este comando (en esta carpeta):" -ForegroundColor Yellow
    Write-Host "    python -m venv .venv" -ForegroundColor Yellow
    Write-Host "y luego vuelve a correr setup_and_run.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Entorno virtual .venv detectado.`n" -ForegroundColor Green

# 2) Instalar dependencias
Write-Host "Instalando dependencias de requirements.txt dentro de .venv..." -ForegroundColor Cyan
& $venvPip install -r requirements.txt

Write-Host "`n[OK] Instalacion de requirements completada.`n" -ForegroundColor Green

# 3) Verificar dependencias clave
$requiredModules = @(
    "requests",
    "tenacity",
    "playwright",
    "dotenv"
)

$missing = @()

Write-Host "Verificando modulos importantes..." -ForegroundColor Cyan

foreach ($mod in $requiredModules) {
    Write-Host ("  - " + $mod + ": ") -NoNewline
    try {
        & $venvPy -c "import importlib; importlib.import_module('$mod')" 2>$null
        Write-Host "OK" -ForegroundColor Green
    } catch {
        Write-Host "FALTA" -ForegroundColor Yellow
        $missing += $mod
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`n[ALERTA] Faltan modulos en .venv:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    Write-Host "Puedes intentar reinstalar con:" -ForegroundColor Yellow
    Write-Host "    $venvPip install " ($missing -join " ") -ForegroundColor Yellow
} else {
    Write-Host "`n[OK] Todos los modulos requeridos estan disponibles." -ForegroundColor Green
}

if ($SoloInstalar) {
    Write-Host "`nModo SoloInstalar activo. No se ejecutara el bot." -ForegroundColor Yellow
    exit 0
}

# 4) Ejecutar el bot con log
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$logFile   = Join-Path $logsDir ("bot_" + $timestamp + ".log")

Write-Host "`nEjecutando el bot y guardando log en: $logFile" -ForegroundColor Cyan

# Comando que se ejecutara dentro de cmd con activacion de .venv
$cmd = @"
cd /d "$PSScriptRoot"
call .venv\Scripts\activate
python -m src.main
"@

cmd.exe /c "$cmd" *>> "$logFile"

Write-Host "`nEjecucion terminada. Revisa el log si hay errores." -ForegroundColor Green
Write-Host "Log: $logFile" -ForegroundColor Green
