# src/logger.py
import logging
import os
from dotenv import load_dotenv

load_dotenv()

def get_logger(name="promo_bot"):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Ya está configurado

    level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger
