# -*- coding: utf-8 -*-
"""
database.py

Base de datos SQLite para almacenar:
- Ofertas publicadas (audit)
- Links afiliados (caché)
- Estadísticas
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DB_FILE = ROOT / "data" / "promo_bot.db"



def init_database():
    """
    Crear base de datos y tablas si no existen.
    
    Ejecutar UNA SOLA VEZ al iniciar.
    """
    if not DB_FILE.parent.exists():
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla 1: Ofertas publicadas (reemplaza audit_offers.csv)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS published_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE,
            title TEXT,
            price REAL,
            original_price REAL,
            discount_pct REAL,
            permalink TEXT,
            link_used TEXT,
            is_affiliate TEXT,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla 2: Links afiliados en caché (reemplaza affiliate_links.csv)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS affiliate_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE,
            original_url TEXT,
            affiliate_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla 3: Productos vistos (dedup)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_products (
            canonical_id TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Crear índices para velocidad
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_id ON published_offers(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON published_offers(published_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_affiliate_url ON affiliate_links(original_url)")
    
    conn.commit()
    conn.close()
    
    print(f"[DB] Base de datos inicializada en {DB_FILE}")


def add_published_offer(item: Dict, discount: float, link_used: str):
    """
    Guardar una oferta publicada en la BD.
    
    Reemplaza: audit_row() de audit.py
    
    Parámetros:
        item: diccionario del producto
        discount: descuento (ej: 0.35 para 35%)
        link_used: URL final que se envió a Telegram
    
    Ejemplo:
        add_published_offer(item, 0.35, "https://mercadolibre.com/sec/...")
    """
    init_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    is_affiliate = "yes" if link_used and link_used.startswith("https://mercadolibre.com/sec/") else "no"
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO published_offers
            (product_id, title, price, original_price, discount_pct, permalink, link_used, is_affiliate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.get("id"),
            item.get("title"),
            item.get("price"),
            item.get("original_price"),
            discount * 100,
            item.get("permalink"),
            link_used,
            is_affiliate
        ))
        conn.commit()
        print(f"[DB] ✓ Oferta guardada: {item.get('id')}")
    except Exception as e:
        print(f"[DB] ✗ Error: {e}")
    finally:
        conn.close()


def add_affiliate_link(product_id: str, original_url: str, affiliate_url: str):
    """
    Guardar link afiliado en caché de BD.
    
    Reemplaza: _save_mapping() de affiliate_runtime.py
    
    Ejemplo:
        add_affiliate_link("MLM123", "https://mercadolibre.com.mx/item/MLM123", 
                           "https://mercadolibre.com/sec/...")
    """
    init_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO affiliate_links
            (product_id, original_url, affiliate_url)
            VALUES (?, ?, ?)
        """, (product_id, original_url, affiliate_url))
        conn.commit()
        print(f"[DB] ✓ Link afiliado guardado: {product_id}")
    except Exception as e:
        print(f"[DB] ✗ Error: {e}")
    finally:
        conn.close()


def get_affiliate_link(original_url: str) -> Optional[str]:
    """
    Obtener link afiliado desde caché de BD.
    
    Reemplaza: _load_map() de affiliate_runtime.py
    
    Retorna: URL afiliada o None si no existe
    
    Ejemplo:
        aff_url = get_affiliate_link("https://mercadolibre.com.mx/item/MLM123")
        if aff_url:
            print(aff_url)
    """
    init_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT affiliate_url FROM affiliate_links WHERE original_url = ? LIMIT 1",
            (original_url,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"[DB] ✗ Error: {e}")
        return None
    finally:
        conn.close()


def get_offer_stats() -> Dict:
    """
    Obtener estadísticas de ofertas publicadas.
    
    Retorna:
        {
            "total_offers": 42,
            "avg_discount_pct": 32.5,
            "avg_price": 2850.0,
            "affiliate_count": 40,
            "affiliate_ratio": 95.2,
            "today_count": 8,
        }
    
    Ejemplo:
        stats = get_offer_stats()
        print(f"Total publicadas: {stats['total_offers']}")
        print(f"Descuento promedio: {stats['avg_discount_pct']}%")
    """
    init_database()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Total
        cursor.execute("SELECT COUNT(*) FROM published_offers")
        total = cursor.fetchone()[0]
        
        # Promedio descuento
        cursor.execute("SELECT AVG(discount_pct) FROM published_offers")
        avg_discount = cursor.fetchone()[0] or 0
        
        # Promedio precio
        cursor.execute("SELECT AVG(price) FROM published_offers")
        avg_price = cursor.fetchone()[0] or 0
        
        # Afiliados
        cursor.execute("SELECT COUNT(*) FROM published_offers WHERE is_affiliate = 'yes'")
        affiliate_count = cursor.fetchone()[0]
        
        # De hoy
        cursor.execute("""
            SELECT COUNT(*) FROM published_offers 
            WHERE DATE(published_at) = DATE('now')
        """)
        today_count = cursor.fetchone()[0]
        
        affiliate_ratio = (affiliate_count / total * 100) if total > 0 else 0
        
        return {
            "total_offers": total,
            "avg_discount_pct": round(avg_discount, 2),
            "avg_price": round(avg_price, 2),
            "affiliate_count": affiliate_count,
            "affiliate_ratio": round(affiliate_ratio, 1),
            "today_count": today_count,
        }
    except Exception as e:
        print(f"[DB] ✗ Error: {e}")
        return {}
    finally:
        conn.close()
        
def is_product_seen_db(canonical_id: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM seen_products WHERE canonical_id = ?", (canonical_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_seen_product_db(canonical_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO seen_products (canonical_id) VALUES (?)", (canonical_id,))
        conn.commit()
    finally:
        conn.close()

def print_stats():
    """
    Imprimir estadísticas lindas en consola.
    
    Ejemplo:
        print_stats()
    """
    stats = get_offer_stats()
    
    print(f"""
╔════════════════════════════════════════╗
║   📊 ESTADÍSTICAS DE OFERTAS           ║
╚════════════════════════════════════════╝

Total publicadas:     {stats['total_offers']} ofertas
Descuento promedio:   {stats['avg_discount_pct']}%
Precio promedio:      ${stats['avg_price']:.0f} MXN
Usando afiliado:      {stats['affiliate_ratio']}%
Publicadas hoy:       {stats['today_count']} ofertas

    """)