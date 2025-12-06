@echo off
title 🧹 MASTER RESET (Limpieza Total + Browser Fix)
color 0C
cls

echo.
echo ============================================
echo   ⚠️ MASTER RESET: LIMPIEZA TOTAL Y REPARACION
echo ============================================
echo.
echo   Esto borrara:
echo   • Historial de publicaciones (DB, CSV, Cache)
echo   • Logs antiguos
echo   • Instalacion de navegadores Playwright (y los reinstalara)
echo.
echo   Se conservara la carpeta 'data_backup/' (si existe).
echo.

set /p CONFIRM="¿Deseas continuar con el RESET TOTAL y la reparacion del navegador? (s/n): "

if /i NOT "%CONFIRM%"=="s" (
    echo ❌ Operacion cancelada.
    timeout /t 2 >nul
    exit /b 1
)

echo.
echo [1/5] Deteniendo procesos Python...
taskkill /f /im python.exe >nul 2>&1
echo ✅ Procesos detenidos.

echo [2/5] Respaldando y limpiando DATA...
REM El script FULL_RESET_PRO.bat ya hace un backup de 'data' en 'data_backup' 
if exist data (
    if exist data_backup rmdir /s /q data_backup >nul 2>&1
    xcopy data data_backup /e /i /h /y >nul
    echo   ✓ Backup listo en data_backup/
)
if exist data (
    del /q "data\*.db" >nul 2>&1
    del /q "data\*.csv" >nul 2>&1
    del /q "data\*.json" >nul 2>&1
    del /q "data\*.log" >nul 2>&1
    echo   ✓ Historial (DB, CSV, JSON) depurado en 'data'.
) else (
    mkdir data
)
if exist ".seen.json" del /f /q ".seen.json" >nul 2>&1

echo [3/5] Eliminando __pycache__ y logs...
for /d /r %%i in (__pycache__) do (if exist "%%i" rmdir /s /q "%%i")
if exist logs rmdir /s /q logs
mkdir logs
echo ✓ Caches de Python y logs antiguos eliminados.

echo [4/5] Depurando cache de Chromedriver (UCD)...
if exist "%LOCALAPPDATA%\undetected_chromedriver" (
    del /q /s "%LOCALAPPDATA%\undetected_chromedriver\*" >nul 2>&1
    for /d %%d in ("%LOCALAPPDATA%\undetected_chromedriver\*") do rmdir /s /q "%%d" >nul 2>&1
    echo ✓ Cache de UCD depurada.
)

echo [5/5] Reinstalando navegadores Playwright...
python -m playwright uninstall --all >nul 2>&1
python -m playwright install chromium
echo ✅ Instalacion de navegadores completada.

echo.
echo ============================================
echo ✅ MASTER RESET COMPLETADO
echo Ejecute BOT.bat de nuevo.
echo ============================================
pause