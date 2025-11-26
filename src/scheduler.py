# -*- coding: utf-8 -*-
"""
scheduler.py

Scheduler automático para ejecutar el bot cada N minutos.
No necesitas estar pendiente, se ejecuta solo.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time


class PromoScheduler:
    """
    Ejecutar función de forma automática cada N minutos.
    
    Uso:
        scheduler = PromoScheduler()
        scheduler.start(job_func, interval_minutes=30)  # Cada 30 min
        scheduler.run_forever()  # Mantener ejecutándose
    """
    
    def __init__(self):
        """Inicializar scheduler"""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def start(self, job_func, interval_minutes: int = 30):
        """
        Comenzar a ejecutar job automáticamente cada N minutos.
        
        Parámetros:
            job_func: función a ejecutar (ej: main_run)
            interval_minutes: cada cuántos minutos (default: 30)
        
        Ejemplo:
            def mi_funcion():
                print("Ejecutándose...")
            
            scheduler = PromoScheduler()
            scheduler.start(mi_funcion, interval_minutes=30)
            scheduler.run_forever()
        """
        try:
            # Agregar job
            self.scheduler.add_job(
                job_func,
                'interval',
                minutes=interval_minutes,
                id='promo_bot_job',
                name=f'Ejecutar cada {interval_minutes} minutos',
                next_run_time=datetime.now(),  # Ejecutar inmediatamente
            )
            
            # Iniciar scheduler
            self.scheduler.start()
            self.is_running = True
            
            print(f"""
╔════════════════════════════════════════╗
║   🤖 SCHEDULER INICIADO                ║
╚════════════════════════════════════════╝

Intervalo: cada {interval_minutes} minutos
Próxima ejecución: AHORA
Status: ✅ EN EJECUCIÓN

Presiona CTRL+C para detener.

            """)
        except Exception as e:
            print(f"[SCHEDULER] ✗ Error al iniciar: {e}")
    
    def run_forever(self):
        """
        Mantener scheduler corriendo indefinidamente.
        
        Presionar CTRL+C para detener.
        """
        if not self.is_running:
            print("[SCHEDULER] ✗ Scheduler no está iniciado")
            return
        
        try:
            # Mantener el programa corriendo
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[SCHEDULER] ⏹️  Deteniendo...")
            self.stop()
    
    def stop(self):
        """Detener el scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("[SCHEDULER] ✓ Detenido correctamente")