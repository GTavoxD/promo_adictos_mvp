@echo off
REM -*- coding: utf-8 -*-
REM RESET CON CONFIRMACIÓN

echo.
echo ============================================
echo   🗑️  RESETEO DE PROYECTO (CON CONFIRMACION)
echo ============================================
echo.
echo ⚠️  ADVERTENCIA:
echo   Esto borrará TODOS los historiales y resetará
echo   el proyecto a estado CERO.
echo.
echo   • Base de datos de vistos
echo   • Caché de enriquecimiento
echo   • Logs antiguos
echo.

set /p CONFIRM="¿Deseas continuar? (s/n): "

if /i not "%CONFIRM%"=="s" (
    echo ❌ Operación cancelada
    pause
    exit /b 1
)

echo.
echo Continuando con reseteo...
echo.

REM [Resto del script igual que arriba]
cd /d "%~dp0"

set DATA_DIR=data
set LOG_DIR=logs
set DB_FILE=data\promo_bot.db
set SEEN_FILE=.seen.json
set CACHE_FILE=data\enrichment_cache.json

echo [1/6] Deteniendo procesos de Python...
taskkill /IM python.exe /F >nul 2>&1
echo ✅ Hecho

echo [2/6] Eliminando base de datos...
if exist "%DB_FILE%" del /f /q "%DB_FILE%" && echo ✅ BD eliminada

echo [3/6] Eliminando caché de visto...
if exist "%SEEN_FILE%" del /f /q "%SEEN_FILE%" && echo ✅ Caché eliminado

echo [4/6] Eliminando caché de enriquecimiento...
if exist "%CACHE_FILE%" del /f /q "%CACHE_FILE%" && echo ✅ Cache enrich eliminado

echo [5/6] Limpiando logs...
if exist "%LOG_DIR%" del /f /q "%LOG_DIR%\*.log" && echo ✅ Logs limpios

echo [6/6] Verificando estructura...
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo ✅ Estructura lista

echo.
echo ✅ RESETEO COMPLETADO
echo.
pause