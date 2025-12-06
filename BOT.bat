@echo off
setlocal enabledelayedexpansion

REM ===============================
REM Configuración de entorno
REM ===============================
set PYTHON_PATH=C:\Users\tavo_\AppData\Local\Programs\Python\Python312\python.exe
set PROJECT_PATH=C:\Users\tavo_\Desktop\promo_adictos_mvp
set BOT_SCRIPT=%PROJECT_PATH%\main.py

REM ===============================
REM CREACIÓN DE DIRECTORIOS ESENCIALES
REM ===============================
if not exist "%PROJECT_PATH%\logs" mkdir "%PROJECT_PATH%\logs"
if not exist "%PROJECT_PATH%\temp" mkdir "%PROJECT_PATH%\temp"
if not exist "%PROJECT_PATH%\backup" mkdir "%PROJECT_PATH%\backup"
echo ✓ Directorios de logs, temp y backup asegurados.

REM ===============================
REM Verificación y Loop principal
REM ===============================
:loop
cls
echo.
echo ========================================
echo Ejecutando PromoAdictos Bot...
echo ========================================
echo Fecha: %date% - Hora: %time%
echo ========================================

REM Pausa remota si existe archivo pause.flag
if exist "%PROJECT_PATH%\pause.flag" (
    echo ⚠️ Archivo pause.flag detectado. Bot pausado manualmente.
    timeout /t 5 > NUL
    goto loop
)

REM El -u obliga a Python a mostrar los textos al instante
REM Quitamos el '2>>' para que los errores salgan en PANTALLA
"%PYTHON_PATH%" -u "%BOT_SCRIPT%"
REM Ejecutar el bot principal
REM Los errores serán registrados en logs/errors.log
"%PYTHON_PATH%" "%BOT_SCRIPT%" 2>> "%PROJECT_PATH%\logs\errors.log"


REM Ejecutar generadores si el bot terminó sin errores
if %ERRORLEVEL% equ 0 (
    "%PYTHON_PATH%" "%PROJECT_PATH%\dashboard_generator.py"
    "%PYTHON_PATH%" "%PROJECT_PATH%\bloqueos_dashboard.py"

    echo ✅ Ciclo finalizado correctamente.
) else (
    echo ⚠️ El script terminó con error. Código de salida: %ERRORLEVEL%
    powershell -c "(New-Object Media.SoundPlayer 'C:\\Windows\\Media\\Windows Error.wav').PlaySync()"
    echo.
    echo Presiona una tecla para ver el error...
    pause >nul
)

REM Guardar resumen de ciclo
echo [%date% %time%] Ciclo terminado con código %ERRORLEVEL% >> "%PROJECT_PATH%\logs\run_history.log"

REM Backup de CSVs importantes
set BACKUP_DIR=%PROJECT_PATH%\backup\%date:/=-%
mkdir "%BACKUP_DIR%" > NUL 2>&1
copy "%PROJECT_PATH%\data\*.csv" "%BACKUP_DIR%\" > NUL

REM Limpieza de archivos temporales
del /q "%PROJECT_PATH%\temp\*" > NUL 2>&1

echo.
echo Fecha: %date% - Hora: %time%
echo 🔁 Reiniciando en 30 segundos...
timeout /t 30 /nobreak > NUL
goto loop