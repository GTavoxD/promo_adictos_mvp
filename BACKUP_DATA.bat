@echo off
title Backup de Sesión Playwright (data\)

set SOURCE=data
set BACKUP=data_backup

echo ============================================
echo   CREANDO BACKUP DE SESION (data/)
echo ============================================

if not exist "%SOURCE%" (
    echo ERROR: No existe la carpeta data/ (no hay sesión que respaldar)
    pause
    exit /b
)

echo - Eliminando backup anterior si existía...
if exist "%BACKUP%" rmdir /s /q "%BACKUP%"

echo - Creando copia nueva...
xcopy "%SOURCE%" "%BACKUP%" /e /i /h /y >nul

echo - Backup creado correctamente en: %BACKUP%

echo ============================================
echo   BACKUP COMPLETADO
echo ============================================

pause
