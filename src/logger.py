# -*- coding: utf-8 -*-
"""
logger.py

Sistema de logging centralizado.
Escribe a archivo y pantalla.
"""

import logging
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"


def setup_logger(name: str = "promo_bot") -> logging.Logger:
    """
    Configurar logger centralizado
    
    Uso:
        from src.logger import setup_logger
        logger = setup_logger()
        logger.info("Mensaje")
        logger.error("Error")
    """
    # Crear carpeta logs/ si no existe
    LOG_DIR.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Evitar duplicados si se llama varias veces
    if logger.hasHandlers():
        return logger
    
    # Handler: archivo
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Handler: consola/terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato del log
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger