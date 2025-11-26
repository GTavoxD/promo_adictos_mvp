# valida_env.py
import os
from dotenv import load_dotenv

try:
    load_dotenv()
    print("✅ .env cargado correctamente")
    
    # Mostrar todas las variables
    for key, value in os.environ.items():
        if not key.startswith("_"):
            print(f"  {key} = {value}")
    
except Exception as e:
    print(f"❌ Error en .env: {e}")