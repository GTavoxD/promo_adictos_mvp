@echo off
cd /d C:\Users\tavo_\Desktop\promo_adictos_mvp

echo Directorio: %cd%
echo.

echo Validando .venv...
if exist ".venv\Scripts\activate.bat" (
    echo OK: .venv existe
) else (
    echo ERROR: .venv NO existe
    pause
    exit /b 1
)

echo.
echo Activando venv...
call .venv\Scripts\activate.bat

echo.
echo Ejecutando bot...
python -m src.main

echo.
pause