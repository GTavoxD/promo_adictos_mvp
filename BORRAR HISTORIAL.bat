@echo off
title Limpiar historial de ofertas - PromoAdictos

cd /d "%~dp0"

echo ================================================
echo   ELIMINANDO HISTORIAL (.seen.json)
echo ================================================
echo.

if exist ".seen.json" (
    del /f /q ".seen.json"
    echo [OK] Archivo .seen.json eliminado.
) else (
    echo [INFO] No existe .seen.json, nada que limpiar.
)

echo.
echo Listo. El bot publicará TODO de nuevo como si fuera la primera vez.
echo.
pause
