@echo off
title Restaurar Sesión Playwright (data_backup → data)

set SOURCE=data_backup
set TARGET=data

echo ============================================
echo   RESTAURANDO SESION PLAYWRIGHT
echo ============================================

if not exist "%SOURCE%" (
    echo ERROR: No existe data_backup (no hay respaldo)
    pause
    exit /b
)

:: Eliminamos data actual
if exist "%TARGET%" (
    echo - Eliminando data/ corrupto...
    rmdir /s /q "%TARGET%"
)

echo - Restaurando desde backup...
xcopy "%SOURCE%" "%TARGET%" /e /i /h /y >nul

echo ============================================
echo   RESTAURACION COMPLETADA
echo ============================================

pause
