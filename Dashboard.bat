@echo off
title PromoAdictos - Dashboard
cd /d C:\Users\tavo_\Desktop\promo_adictos_mvp

echo ============================================
echo   PromoAdictos - Dashboard
echo   - Busca ofertas
echo ============================================
echo.

echo [%date% %time%] Generando HTML...
python dashboard_generator.py

:: CHOICE espera hasta 5s. Si presionas S, sale de inmediato.
choice /C S0 /N /T 3 /D 0 >nul

echo.
echo [%date% %time%] Iniciando Dashboard.
start dashboard.html



