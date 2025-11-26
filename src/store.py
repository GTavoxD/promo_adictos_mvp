# -*- coding: utf-8 -*-
"""
Cache de productos vistos para evitar duplicados
Guarda títulos Y links en BD SQLite
Duración configurable por .env
"""

import sqlite3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

DB_PATH = os.getenv("DATABASE_PATH", "data/promo_bot.db")

# ============================
# INICIALIZACIÓN
# ============================

def init_title_cache():
    """Crear tabla si no existe, o migrar si tiene estructura vieja"""
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Verificar si la tabla existe y tiene la estructura correcta
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='seen_products'
    """)
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Verificar si tiene la columna 'title'
        cursor.execute("PRAGMA table_info(seen_products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'title' not in columns:
            # Tabla vieja, eliminar y recrear
            print("[CACHE] ⚠️ Tabla con estructura vieja, recreando...")
            cursor.execute("DROP TABLE seen_products")
            db.commit()
            table_exists = False
    
    if not table_exists:
        # Crear tabla con estructura correcta
        cursor.execute("""
            CREATE TABLE seen_products (
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (title, link)
            )
        """)
        db.commit()
        print("[CACHE] ✅ Tabla seen_products creada correctamente")
    
    db.close()
    
# ============================
# VERIFICAR SI FUE VISTO
# ============================

def is_product_seen(title: str, link: str, hours: int = None) -> bool:
    """
    Verifica si un PRODUCTO (título + link) ya fue visto recientemente.
    
    Lee la duración del caché desde .env (CACHE_TTL_DAYS)
    
    Args:
        title: Título del producto
        link: URL del producto
        hours: Horas hacia atrás a buscar (default: desde .env o 720 = 30 días)
    
    Returns:
        True si fue visto recientemente, False si es nuevo
    """
    
    if not title or not link:
        return False
    
    title_lower = title.lower().strip()
    link_lower = link.lower().strip()
    
    # ✅ Obtener duración del caché desde .env
    if hours is None:
        load_dotenv()
        cache_days = int(os.getenv("CACHE_TTL_DAYS", "30"))
        hours = cache_days * 24
    
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        # Buscar combinación exacta de título + link
        cursor.execute("""
            SELECT first_seen FROM seen_products 
            WHERE LOWER(TRIM(title)) = ? AND LOWER(TRIM(link)) = ?
            LIMIT 1
        """, (title_lower, link_lower))
        
        row = cursor.fetchone()
        
        if not row:
            db.close()
            return False  # ✅ Producto NO visto (es nuevo)
        
        # Verificar si está dentro del rango horario
        first_seen = datetime.fromisoformat(row[0])
        cutoff = datetime.now() - timedelta(hours=hours)
        
        db.close()
        
        if first_seen > cutoff:
            return True  # ❌ Visto recientemente (dentro del cache)
        else:
            return False  # ✅ Pasó el tiempo, considerarlo NUEVO
    
    except Exception as e:
        print(f"[CACHE] Error verificando producto: {e}")
        return False


def is_title_seen(title: str, hours: int = None) -> bool:
    """
    Verifica si un TÍTULO ya fue visto (sin importar el link).
    Útil para detectar el mismo producto en diferentes ofertas.
    """
    
    if not title:
        return False
    
    title_lower = title.lower().strip()
    
    # ✅ Obtener duración del caché desde .env
    if hours is None:
        load_dotenv()
        cache_days = int(os.getenv("CACHE_TTL_DAYS", "30"))
        hours = cache_days * 24
    
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        # Buscar el título (sin importar el link)
        cursor.execute("""
            SELECT first_seen FROM seen_products 
            WHERE LOWER(TRIM(title)) = ?
            LIMIT 1
        """, (title_lower,))
        
        row = cursor.fetchone()
        db.close()
        
        if not row:
            return False  # ✅ Título NO visto
        
        # Verificar si está dentro del rango horario
        first_seen = datetime.fromisoformat(row[0])
        cutoff = datetime.now() - timedelta(hours=hours)
        
        if first_seen > cutoff:
            return True  # ❌ Visto recientemente
        else:
            return False  # ✅ Pasó el tiempo
    
    except Exception as e:
        print(f"[CACHE] Error verificando título: {e}")
        return False


def is_link_seen(link: str, hours: int = None) -> bool:
    """
    Verifica si un LINK ya fue visto (sin importar el título).
    Útil para detectar el mismo producto con títulos diferentes.
    """
    
    if not link:
        return False
    
    link_lower = link.lower().strip()
    
    # ✅ Obtener duración del caché desde .env
    if hours is None:
        load_dotenv()
        cache_days = int(os.getenv("CACHE_TTL_DAYS", "30"))
        hours = cache_days * 24
    
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        # Buscar el link (sin importar el título)
        cursor.execute("""
            SELECT first_seen FROM seen_products 
            WHERE LOWER(TRIM(link)) = ?
            LIMIT 1
        """, (link_lower,))
        
        row = cursor.fetchone()
        db.close()
        
        if not row:
            return False  # ✅ Link NO visto
        
        # Verificar si está dentro del rango horario
        first_seen = datetime.fromisoformat(row[0])
        cutoff = datetime.now() - timedelta(hours=hours)
        
        if first_seen > cutoff:
            return True  # ❌ Visto recientemente
        else:
            return False  # ✅ Pasó el tiempo
    
    except Exception as e:
        print(f"[CACHE] Error verificando link: {e}")
        return False

# ============================
# AGREGAR A CACHÉ
# ============================

def add_product_to_cache(title: str, link: str) -> bool:
    """
    Agrega un PRODUCTO (título + link) al caché.
    
    Args:
        title: Título del producto
        link: URL del producto
    
    Returns:
        True si se agregó, False si ya existía
    """
    
    if not title or not link:
        return False
    
    title_lower = title.lower().strip()
    link_lower = link.lower().strip()
    
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        # Intentar insertar (si ya existe, falla por PRIMARY KEY)
        cursor.execute("""
            INSERT INTO seen_products (title, link, first_seen, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (title_lower, link_lower))
        
        db.commit()
        db.close()
        return True  # ✅ Nuevo producto agregado
    
    except sqlite3.IntegrityError:
        # Ya existe, actualizar last_seen
        try:
            db = sqlite3.connect(DB_PATH)
            cursor = db.cursor()
            cursor.execute("""
                UPDATE seen_products 
                SET last_seen = CURRENT_TIMESTAMP
                WHERE LOWER(TRIM(title)) = ? AND LOWER(TRIM(link)) = ?
            """, (title_lower, link_lower))
            db.commit()
            db.close()
        except:
            pass
        return False
    except Exception as e:
        print(f"[CACHE] Error agregando producto: {e}")
        return False

# ============================
# LIMPIAR CACHÉ
# ============================

def clear_product_cache():
    """Limpia TODOS los productos del caché"""
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute("DELETE FROM seen_products")
        db.commit()
        db.close()
        print("[CACHE] ✅ Caché de productos limpiado completamente")
        return True
    except Exception as e:
        print(f"[CACHE] Error limpiando caché: {e}")
        return False


def clear_old_cache(days: int = None):
    """
    Limpia productos más viejos que X días
    
    Args:
        days: Días a mantener (default: desde .env CACHE_TTL_DAYS)
    """
    
    # ✅ Obtener días desde .env
    if days is None:
        load_dotenv()
        days = int(os.getenv("CACHE_TTL_DAYS", "30"))
    
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        cursor.execute("""
            DELETE FROM seen_products 
            WHERE first_seen < ?
        """, (cutoff.isoformat(),))
        
        deleted = cursor.rowcount
        db.commit()
        db.close()
        
        print(f"[CACHE] 🗑️ Limpiados {deleted} productos más viejos que {days} días")
        return deleted
    except Exception as e:
        print(f"[CACHE] Error limpiando caché antiguo: {e}")
        return 0

# ============================
# ESTADÍSTICAS
# ============================

def get_cache_stats() -> dict:
    """
    Retorna estadísticas del caché
    
    Returns:
        Dict con total_cached y added_today
    """
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        
        # Total de productos en caché
        cursor.execute("SELECT COUNT(*) FROM seen_products")
        total = cursor.fetchone()[0]
        
        # Productos agregados hoy
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM seen_products 
            WHERE DATE(first_seen) = ?
        """, (today,))
        today_count = cursor.fetchone()[0]
        
        # Productos agregados esta semana
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) FROM seen_products 
            WHERE DATE(first_seen) >= ?
        """, (week_ago,))
        week_count = cursor.fetchone()[0]
        
        db.close()
        
        return {
            "total_cached": total,
            "added_today": today_count,
            "added_this_week": week_count
        }
    except Exception as e:
        print(f"[CACHE] Error obteniendo stats: {e}")
        return {
            "total_cached": 0,
            "added_today": 0,
            "added_this_week": 0
        }


def print_cache_stats():
    """Imprime estadísticas del caché de forma legible"""
    stats = get_cache_stats()
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS DEL CACHÉ")
    print("="*50)
    print(f"Total en caché: {stats['total_cached']} productos")
    print(f"Agregados hoy: {stats['added_today']} productos")
    print(f"Agregados esta semana: {stats['added_this_week']} productos")
    print("="*50 + "\n")

# ============================
# COMPATIBILIDAD
# ============================

def seen_keep(canonical_id: str) -> bool:
    """
    Función legacy (por compatibilidad)
    Ahora solo retorna False para no bloquear
    """
    return False