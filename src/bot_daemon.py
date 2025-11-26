# -*- coding: utf-8 -*-
"""
bot_daemon.py

Punto de entrada para ejecutar el bot AUTOMÁTICAMENTE cada N minutos.

Uso:
    python bot_daemon.py

El bot se ejecutará automáticamente cada 30 minutos hasta que presiones CTRL+C.
"""

import os
import sys
from pathlib import Path

# Agregar ruta del proyecto
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.scheduler import PromoScheduler
from main import run


def main():
    """Punto de entrada principal"""
    
    print("""
╔════════════════════════════════════════════╗
║   🎯 PROMO ADICTOS - BOT AUTOMÁTICO       ║
╚════════════════════════════════════════════╝
    """)
    
    # Crear scheduler
    scheduler = PromoScheduler()
    
    # Obtener intervalo de .env (default: 30 minutos)
    try:
        interval = int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "30") or 30)
    except Exception:
        interval = 30
    
    print(f"⏰ Intervalo configurado: {interval} minutos\n")
    
    # Iniciar scheduler
    scheduler.start(run, interval_minutes=interval)
    
    # Mantener ejecutándose
    try:
        scheduler.run_forever()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        scheduler.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()