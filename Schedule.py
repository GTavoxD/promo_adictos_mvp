# schedule.py
import schedule
import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

def run_bot():
    logger.info("Ejecutando bot...")
    subprocess.run(["python", "main.py"])
    logger.info("Bot completado")

# Ejecutar cada 60 minutos
schedule.every(60).minutes.do(run_bot)

logger.info("Scheduler iniciado - ejecutará cada 60 minutos")

while True:
    schedule.run_pending()
    time.sleep(1)