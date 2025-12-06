@echo off
title 🧹 RESET TOTAL - PROMO ADICTOS
color 0B
cls

echo.
echo ===========================================
echo   🗑️  RESETEO COMPLETO (Historial y Caché)
echo ===========================================
echo.
echo ⚠️ ADVERTENCIA:
echo   Esto borrará todo el historial de precios y productos vistos:
echo   • Base de datos (promo_bot.db)
echo   • Logs y caches de seguimiento (.json, .csv)
echo   • Cache de navegadores (Undetected Chromedriver)
echo   (Se conserva el estado de sesion si existe en 'data/')
echo.

REM Confirmación del usuario
set /p CONFIRM="¿Deseas continuar con el reseteo? (s/n): "

if /i NOT "%CONFIRM%"=="s" (
    echo ❌ Operación cancelada.
    timeout /t 2 >nul
    exit /b 1
)

echo.
echo [1/5] Deteniendo procesos Python...
taskkill /f /im python.exe >nul 2>&1
echo ✅ Procesos detenidos.

echo [2/5] Limpiando historial y logs de la carpeta 'data'...
REM Preserva la carpeta 'data' pero elimina DBs, CSVs, y JSONs de seguimiento.
if exist "data" (
    del /q "data\promo_bot.db" >nul 2>&1
    del /q "data\*.csv" >nul 2>&1
    del /q "data\*.json" >nul 2>&1
    del /q "data\*.log" >nul 2>&1
    echo ✓ Historial (DB, CSV, JSON) depurado en 'data'.
) else (
    mkdir data
    echo ✓ Carpeta 'data' creada.
)
REM Eliminar archivos de seguimiento antiguos en la raíz
if exist ".seen.json" del /f /q ".seen.json" >nul 2>&1
echo ✓ Archivos de caché antiguos eliminados.

echo [3/5] Depurando caché de navegadores...
REM Eliminar caché de Playwright/Selenium
if exist "selenium\cache\" rmdir /s /q "selenium\cache" >nul 2>&1
REM Eliminar caché de Undetected Chromedriver (UCD)
if exist "%LOCALAPPDATA%\undetected_chromedriver" (
    rem Borrar todo el contenido binario
    del /q /s "%LOCALAPPDATA%\undetected_chromedriver\*" >nul 2>&1
    for /d %%d in ("%LOCALAPPDATA%\undetected_chromedriver\*") do rmdir /s /q "%%d" >nul 2>&1
)
echo ✓ Caché de navegación depurada.

echo [4/5] Limpiando archivos compilados (__pycache__)...
for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        rmdir /s /q "%%i"
    )
)
echo ✓ __pycache__ eliminado.

echo [5/5] Verificando estructura...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
echo ✓ Estructura de carpetas verificada.

echo.
echo ============================================
echo ✅ RESETEO COMPLETO FINALIZADO
echo El bot volverá a publicar TODO.
echo ============================================
pause