@echo off
title PromoAdictos - FULL RESET PRO (Seguro + Backup)

echo ============================================
echo     FULL RESET PRO - LIMPIEZA SEGURA
echo     * Conserva sesión Playwright
echo     * Backup automático: data_backup
echo ============================================
echo.

cd /d C:\Users\tavo_\Desktop\promo_adictos_mvp

:: ---------------------------------------------
:: 0. Crear backup de la sesión
:: ---------------------------------------------
echo - Respaldando carpeta data/
if exist data (
    if exist data_backup rmdir /s /q data_backup
    xcopy data data_backup /e /i /h /y >nul
    echo   Backup listo en data_backup/
) else (
    echo   No existe data/ (no hay sesión que respaldar)
)

:: ---------------------------------------------
:: 1. Borrar archivo seen.json
:: ---------------------------------------------
if exist seen.json del /f /q seen.json

:: ---------------------------------------------
:: 2. Borrar audit.csv
:: ---------------------------------------------
if exist audit.csv del /f /q audit.csv

:: ---------------------------------------------
:: 3. Nunca borrar carpeta data/ (almacena tu sesión)
:: ---------------------------------------------
echo - Carpeta data/ CONSERVADA

:: ---------------------------------------------
:: 4. Borrar carpeta logs/
:: ---------------------------------------------
if exist logs rmdir /s /q logs

echo.
echo ============================================
echo     FULL RESET PRO COMPLETADO
echo     Tu sesión Playwright está a salvo.
echo     Backup disponible en data_backup/
echo ============================================

pause
