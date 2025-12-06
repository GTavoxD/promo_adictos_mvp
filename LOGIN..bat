@echo off
echo ==========================================
echo   LOGIN MANUAL (MODO ANTI-DETECT)
echo ==========================================
echo.
echo Esto abrira un navegador especial que permite cargar el CAPTCHA.
echo.
pause

REM Ejecutamos el script Python que creamos en el paso 1
python src/manual_login.py

echo.
pause