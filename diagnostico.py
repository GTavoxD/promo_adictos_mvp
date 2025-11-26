import os
import sys
from pathlib import Path

root = Path(__file__).parent
sys.path.insert(0, str(root))

print("Raiz: " + str(root))

from dotenv import load_dotenv
load_dotenv()

print("OK - .env cargado")

from src.database import init_database
print("OK - database.init_database importado")

init_database()
print("OK - BD inicializada")

import sqlite3

db_path = os.getenv("DATABASE_PATH", "data/promo_bot.db")
print("BD path: " + db_path)

try:
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    # Ver ESTRUCTURA de seen_products
    print("\n" + "="*50)
    print("ESTRUCTURA de tabla seen_products:")
    print("="*50)
    
    cursor.execute("PRAGMA table_info(seen_products)")
    columns = cursor.fetchall()
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        print(f"  - {col_name} ({col_type})")
    
    # Contar items
    cursor.execute("SELECT COUNT(*) FROM seen_products")
    count = cursor.fetchone()[0]
    print(f"\nItems en cache: {count}")
    
    if count > 0:
        # Mostrar ultimos 5
        cursor.execute("SELECT * FROM seen_products ORDER BY datetime(first_seen) DESC LIMIT 5")
        rows = cursor.fetchall()
        
        print("\nUltimos 5 items:")
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row}")
    
    # Opcion de limpiar
    print("\n" + "="*50)
    resp = input("Limpiar tabla seen_products? (s/n): ")
    if resp.lower() == 's':
        cursor.execute("DELETE FROM seen_products")
        db.commit()
        print("OK - Tabla limpiada")
        print("Los productos seran considerados NUEVOS en el proximo ciclo")
    
    db.close()
    print("\nOK - Diagnostico completado")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()