@echo off
REM -*- coding: utf-8 -*-
REM =====================================================
REM PROMO ADICTOS - BOT EN LOOP (VERSIÓN COMPATIBLE)
REM =====================================================

setlocal enabledelayedexpansion

:: Configuración del proyecto
set PROJECT_DIR=C:\Users\tavo_\Desktop\promo_adictos_mvp
set VENV_PATH=%PROJECT_DIR%\.venv\Scripts\activate.bat
set LOG_DIR=%PROJECT_DIR%\logs

:: Configuración del ciclo
set CYCLE_INTERVAL=3600
set SKIP_WAIT=10
set MAX_RETRIES=3

title PromoAdictos - Bot en Loop

:: Crear carpeta de logs si no existe
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo.
echo ============================================
echo    PROMO ADICTOS - BOT EN LOOP
echo ============================================
echo.
echo    Proyecto: %PROJECT_DIR%
echo    Intervalo: %CYCLE_INTERVAL%s (60 min)
echo    Skip con: S + Enter
echo    Logs: %LOG_DIR%
echo.
echo ============================================
echo.

:: Validar entorno virtual
if not exist "%VENV_PATH%" (
    echo ERROR: No se encontro el entorno virtual
    echo Ruta esperada: %VENV_PATH%
    echo.
    pause
    exit /b 1
)

echo Entorno virtual encontrado: OK
echo.

:: Cambiar directorio
cd /d "%PROJECT_DIR%"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo acceder a %PROJECT_DIR%
    pause
    exit /b 1
)

echo Directorio actual: OK
echo.

:: Activar entorno virtual
call "%VENV_PATH%"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo Entorno virtual activado: OK
echo.

:: =====================================================
:: LOOP PRINCIPAL
:: =====================================================

:loop

set CURRENT_TIME=%date% %time%
set RETRY_COUNT=0

:retry_loop

if %RETRY_COUNT% gtr %MAX_RETRIES% (
    echo.
    echo ERROR: Maximo de reintentos alcanzado (%MAX_RETRIES%)
    echo Se ejecutara siguiente ciclo en 10s...
    echo.
    timeout /t 10 /nobreak
    set RETRY_COUNT=0
    goto loop
)

echo.
echo [%CURRENT_TIME%] Ejecutando ciclo #%RETRY_COUNT%...
echo ============================================
echo.

:: Ejecutar bot
python -m src.main
set BOT_EXIT_CODE=!errorlevel!

echo.

:: Validar resultado
if !BOT_EXIT_CODE! equ 0 (
    echo.
    echo [%CURRENT_TIME%] EXITO: Ciclo completado
    echo.
) else (
    set /a RETRY_COUNT+=1
    echo.
    echo ADVERTENCIA: Error en ciclo (codigo: !BOT_EXIT_CODE!)
    echo.
    
    if !RETRY_COUNT! leq %MAX_RETRIES% (
        echo Reintentando... (intento !RETRY_COUNT!/%MAX_RETRIES%)
        echo.
        timeout /t 15 /nobreak
        goto retry_loop
    ) else (
        echo ERROR: Maximo de reintentos alcanzado
        echo.
    )
)

echo.
echo ============================================
echo OPCIONES:
echo  [S] + Enter = SALTAR espera (siguiente ciclo ya)
echo  [C] + Enter = CANCELAR (cierra el bot)
echo  [Enter]     = Continuar automaticamente en %SKIP_WAIT%s
echo ============================================
echo.

:: CHOICE compatible
choice /C SC0 /N /T %SKIP_WAIT% /D 0 /M "Selecciona opcion (timeout en %SKIP_WAIT%s)..."

if errorlevel 3 (
    REM Opción 0 (timeout automático)
    echo.
    echo Espera completada, siguiente ciclo...
    echo.
    goto loop
) else if errorlevel 2 (
    REM Opción C (cancelar)
    echo.
    echo Bot cancelado por usuario.
    echo.
    pause
    exit /b 0
) else if errorlevel 1 (
    REM Opción S (skip)
    echo.
    echo SKIP manual - siguiente ciclo inmediato
    echo.
    goto loop
)

goto loop