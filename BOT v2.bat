@echo off
REM ========================================
REM PromoAdictos - Bot + Dashboard Auto-Ejecutor
REM ========================================

setlocal enabledelayedexpansion

REM Colores (opcional)
color 0A

REM ========================================
REM CONFIGURACIÓN
REM ========================================

set PYTHON_PATH=C:\Users\tavo_\AppData\Local\Programs\Python\Python312\python.exe
set PROJECT_PATH=C:\Users\tavo_\Desktop\promo_adictos_mvp
set BOT_SCRIPT=%PROJECT_PATH%\main.py

REM ========================================
REM VERIFICAR QUE PYTHON EXISTE
REM ========================================

if not exist "%PYTHON_PATH%" (
    echo.
    echo ❌ ERROR: Python no encontrado en %PYTHON_PATH%
    echo Modifica PYTHON_PATH en este archivo
    pause
    exit /b 1
)

REM ========================================
REM VERIFICAR QUE LOS SCRIPTS EXISTEN
REM ========================================

if not exist "%BOT_SCRIPT%" (
    echo.
    echo ❌ ERROR: main.py no encontrado en %PROJECT_PATH%
    pause
    exit /b 1
)

REM ========================================
REM LOOP INFINITO: EJECUTAR BOT CONTINUAMENTE
REM ========================================

:loop

echo.
echo ========================================
echo 🤖 Ejecutando ciclo del Bot...
echo ========================================
echo Hora: %date% %time%
echo ========================================
echo.

REM Ejecutar el bot
call "%PYTHON_PATH%" "%BOT_SCRIPT%"

REM Capturar el código de salida
set EXIT_CODE=!ERRORLEVEL!

if !EXIT_CODE! equ 0 (
    echo.
    echo ✅ Ciclo completado exitosamente
) else (
    echo.
    echo ⚠️ Ciclo terminó con código: !EXIT_CODE!
)

echo.
echo ========================================
echo ⏳ Esperando 60 segundos antes de reiniciar...
echo ========================================
echo.

REM Esperar 10 segundos
timeout /t 10 /nobreak

REM Reiniciar el loop
goto loop

REM ========================================
REM FIN
REM ========================================

:end
echo.
echo ❌ Bot terminado
pause