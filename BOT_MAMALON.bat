@echo off
title PromoAdictos - Bot en loop
cd /d C:\Users\tavo_\Desktop\promo_adictos_mvp

:: Activar entorno virtual
call .venv\Scripts\activate.bat

echo ============================================
echo   PromoAdictos - BOT EN LOOP
echo   - Busca ofertas
echo   - Genera link de afiliado (si aplica)
echo   - Publica en Telegram
echo   - Repite cada 60 minutos
echo   - Permite SKIP de ronda con la tecla S
echo ============================================
echo.

:loop
echo [%date% %time%] Ejecutando bot...
python -m main

echo.
echo [%date% %time%] Ciclo terminado.
echo.
echo [PROMOADICTOS] Presiona S para saltar la espera de 10 seg
echo                o no presiones nada para que se ejecute solo.
echo.

:: CHOICE espera hasta 10s. Si presionas S, sale de inmediato.
choice /C S0 /N /T 10 /D 0 >nul

if errorlevel 2 (
    rem Opción 0 (timeout) -> pasó la hora completa
    echo [PROMOADICTOS] Espera completa, iniciando siguiente ciclo...
) else (
    rem Opción S -> skip manual
    echo [PROMOADICTOS] SKIP manual, iniciando siguiente ciclo...
)

echo.
goto loop
