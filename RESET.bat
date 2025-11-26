@echo off
REM -*- coding: utf-8 -*-
REM =====================================================
REM RESET PROYECTO PROMO ADICTOS
REM Borra historiales y bases de datos para empezar de cero
REM =====================================================

echo.
echo ============================================
echo   🗑️  RESETEO DE PROYECTO PROMO ADICTOS
echo ============================================
echo.

REM Cambiar a la carpeta del script
cd /d "%~dp0"

REM Variables de rutas
set DATA_DIR=data
set LOG_DIR=logs
set DB_FILE=data\promo_bot.db
set SEEN_FILE=.seen.json
set CACHE_FILE=data\enrichment_cache.json

echo [1/6] Deteniendo procesos de Python...
taskkill /IM python.exe /F >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Procesos detenidos
) else (
    echo ℹ️  No hay procesos de Python activos
)

echo.
echo [2/6] Eliminando base de datos SQLite...
if exist "%DB_FILE%" (
    del /f /q "%DB_FILE%"
    echo ✅ BD eliminada: %DB_FILE%
) else (
    echo ℹ️  BD no encontrada: %DB_FILE%
)

echo.
echo [3/6] Eliminando caché de visto (.seen.json)...
if exist "%SEEN_FILE%" (
    del /f /q "%SEEN_FILE%"
    echo ✅ Caché eliminado: %SEEN_FILE%
) else (
    echo ℹ️  Caché no encontrada: %SEEN_FILE%
)

echo.
echo [4/6] Eliminando caché de enriquecimiento...
if exist "%CACHE_FILE%" (
    del /f /q "%CACHE_FILE%"
    echo ✅ Caché enriquecimiento eliminado: %CACHE_FILE%
) else (
    echo ℹ️  Caché enriquecimiento no encontrada: %CACHE_FILE%
)

echo.
echo [5/6] Limpiando logs antiguos...
if exist "%LOG_DIR%" (
    del /f /q "%LOG_DIR%\*.log"
    echo ✅ Logs limpios
) else (
    echo ℹ️  Carpeta logs no encontrada
)

echo.
echo [6/6] Verificando/creando estructura de carpetas...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo ✅ Estructura lista

echo.
echo ============================================
echo   ✅ RESETEO COMPLETADO
echo ============================================
echo.
echo 📊 Estado:
echo   • Base de datos: 🆕 NUEVA
echo   • Historiales: 🗑️  LIMPIADOS
echo   • Caché: 🗑️  LIMPIADOS
echo   • Próxima ejecución: 🚀 DESDE CERO
echo.
echo 💡 Para iniciar el bot:
echo    python main.py
echo.
pause