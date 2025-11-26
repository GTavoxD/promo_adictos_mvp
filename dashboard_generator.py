# -*- coding: utf-8 -*-
"""
dashboard_generator.py
Genera el dashboard HTML profesional con datos en tiempo real
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import json

# Rutas
DB_PATH = "data/promo_bot.db"
DASHBOARD_PATH = "dashboard.html"

def check_database_structure():
    """Verifica la estructura de la base de datos"""
    if not os.path.exists(DB_PATH):
        print(f"❌ No existe la base de datos: {DB_PATH}")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Obtener información de la tabla published_offers
        cursor.execute("PRAGMA table_info(published_offers)")
        columns = cursor.fetchall()
        
        print("📊 Estructura de la tabla published_offers:")
        column_names = []
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            column_names.append(col[1])
        
        return column_names
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return None
    finally:
        conn.close()

def get_database_stats():
    """Obtiene estadísticas de la base de datos"""
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    try:
        # Total de ofertas
        cursor.execute("SELECT COUNT(*) FROM published_offers")
        stats['total_offers'] = cursor.fetchone()[0] or 0
        
        # Ofertas de hoy
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM published_offers WHERE DATE(published_at) = ?", (today,))
        stats['offers_today'] = cursor.fetchone()[0] or 0
        
        # Promedio de descuento - intentar con diferentes nombres de columna
        discount_col = None
        for col_name in ['discount_percentage', 'discount_pct', 'discount', 'descuento']:
            try:
                cursor.execute(f"SELECT AVG({col_name}) FROM published_offers WHERE {col_name} > 0")
                avg_discount = cursor.fetchone()[0]
                if avg_discount is not None:
                    discount_col = col_name
                    stats['avg_discount'] = round(avg_discount, 1)
                    break
            except:
                continue
        
        if 'avg_discount' not in stats:
            stats['avg_discount'] = 0
        
        # Precio promedio - intentar con diferentes nombres
        for col_name in ['final_price', 'price_final', 'price', 'precio']:
            try:
                cursor.execute(f"SELECT AVG({col_name}) FROM published_offers WHERE {col_name} > 0")
                avg_price = cursor.fetchone()[0]
                if avg_price is not None:
                    stats['avg_price'] = round(avg_price, 2)
                    break
            except:
                continue
        
        if 'avg_price' not in stats:
            stats['avg_price'] = 0
        
        # Ratio de afiliados
        try:
            cursor.execute("SELECT COUNT(*) FROM published_offers WHERE affiliate_url LIKE '%/sec/%'")
            with_affiliate = cursor.fetchone()[0] or 0
            stats['affiliate_ratio'] = round((with_affiliate / max(stats['total_offers'], 1)) * 100, 1)
        except:
            stats['affiliate_ratio'] = 0
        
        # Productos en caché
        try:
            cursor.execute("SELECT COUNT(*) FROM seen_products")
            stats['cache_count'] = cursor.fetchone()[0] or 0
        except:
            stats['cache_count'] = 0
        
        # Cálculos adicionales
        if stats['offers_today'] > 0:
            hours_passed = datetime.now().hour or 1
            stats['hourly_rate'] = round(stats['offers_today'] / hours_passed, 1)
        else:
            stats['hourly_rate'] = 0
        
        # Uptime simulado
        stats['uptime'] = datetime.now().hour
        stats['success_rate'] = 98.5
        
        # Tamaño del caché
        if os.path.exists(DB_PATH):
            stats['cache_size'] = round(os.path.getsize(DB_PATH) / (1024*1024), 1)
        else:
            stats['cache_size'] = 0
        
    except Exception as e:
        print(f"Error general obteniendo stats: {e}")
        # Valores por defecto
        return {
            'total_offers': 0,
            'offers_today': 0,
            'avg_discount': 0,
            'avg_price': 0,
            'affiliate_ratio': 0,
            'cache_count': 0,
            'hourly_rate': 0,
            'uptime': 0,
            'success_rate': 0,
            'cache_size': 0
        }
    finally:
        conn.close()
    
    return stats

def get_all_offers_simple():
    """Obtiene todas las ofertas con la estructura real de la BD"""
    if not os.path.exists(DB_PATH):
        return [], []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    all_offers = []
    
    try:
        # Obtener TODAS las columnas disponibles
        cursor.execute("SELECT * FROM published_offers ORDER BY published_at DESC LIMIT 100")
        rows = cursor.fetchall()
        
        # Obtener nombres de columnas
        cursor.execute("PRAGMA table_info(published_offers)")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        print(f"✅ Columnas encontradas: {column_names}")
        
        # Convertir cada fila a diccionario
        for row in rows:
            offer = {}
            for i, col_name in enumerate(column_names):
                offer[col_name] = row[i]
            all_offers.append(offer)
        
        if all_offers:
            print(f"✅ Se encontraron {len(all_offers)} ofertas")
            print(f"📝 Ejemplo de oferta: {list(all_offers[0].keys())}")
        
    except Exception as e:
        print(f"❌ Error obteniendo ofertas: {e}")
    finally:
        conn.close()
    
    return all_offers, column_names

def get_top_discounts(limit=10):
    """Obtiene las mejores ofertas por descuento (adaptado)"""
    all_offers, column_names = get_all_offers_simple()
    
    if not all_offers:
        return []
    
    # Identificar columnas relevantes
    title_col = next((c for c in column_names if 'title' in c.lower()), None)
    discount_col = next((c for c in column_names if 'discount' in c.lower() or 'descuento' in c.lower()), None)
    price_col = next((c for c in column_names if 'price' in c.lower() or 'precio' in c.lower()), None)
    
    offers = []
    for offer in all_offers[:limit]:
        try:
            offers.append({
                'title': offer.get(title_col, offer.get('title', 'Sin título')),
                'discount_pct': round(float(offer.get(discount_col, 0) or 0)),
                'price_final': float(offer.get(price_col, 0) or 0),
                'published_at': offer.get('published_at', ''),
                'affiliate_url': offer.get('affiliate_url', ''),
                'promo_tag': offer.get('promo_tag', '')
            })
        except:
            continue
    
    # Ordenar por descuento
    offers.sort(key=lambda x: x['discount_pct'], reverse=True)
    
    return offers[:limit]

def get_recent_offers(limit=10):
    """Obtiene las ofertas más recientes (adaptado)"""
    all_offers, column_names = get_all_offers_simple()
    
    if not all_offers:
        return []
    
    # Identificar columnas relevantes
    title_col = next((c for c in column_names if 'title' in c.lower()), None)
    discount_col = next((c for c in column_names if 'discount' in c.lower() or 'descuento' in c.lower()), None)
    price_col = next((c for c in column_names if 'price' in c.lower() or 'precio' in c.lower()), None)
    
    offers = []
    for offer in all_offers[:limit]:
        try:
            # Calcular tiempo transcurrido
            time_ago = "Reciente"
            try:
                pub_time = datetime.fromisoformat(str(offer.get('published_at', '')))
                diff = datetime.now() - pub_time
                if diff.days > 0:
                    time_ago = f"Hace {diff.days} días"
                elif diff.seconds > 3600:
                    time_ago = f"Hace {diff.seconds // 3600} horas"
                else:
                    time_ago = f"Hace {diff.seconds // 60} minutos"
            except:
                pass
            
            offers.append({
                'title': offer.get(title_col, offer.get('title', 'Sin título')),
                'discount_pct': round(float(offer.get(discount_col, 0) or 0)),
                'price_final': float(offer.get(price_col, 0) or 0),
                'published_at': offer.get('published_at', ''),
                'time_ago': time_ago,
                'affiliate_url': offer.get('affiliate_url', '')
            })
        except Exception as e:
            print(f"Error procesando oferta: {e}")
            continue
    
    return offers

def get_chart_data():
    """Obtiene datos para las gráficas"""
    if not os.path.exists(DB_PATH):
        return [], [], [], []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    chart_labels = []
    chart_data = []
    
    try:
        # Datos de últimos 7 días
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i))
            date_str = date.strftime('%Y-%m-%d')
            day_name = date.strftime('%a')
            
            chart_labels.append(day_name)
            
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM published_offers WHERE DATE(published_at) = ?", 
                    (date_str,)
                )
                count = cursor.fetchone()[0] or 0
                chart_data.append(count)
            except:
                chart_data.append(0)
    except Exception as e:
        print(f"Error obteniendo datos de gráfica: {e}")
        chart_labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        chart_data = [0, 0, 0, 0, 0, 0, 0]
    finally:
        conn.close()
    
    # Categorías (simulado por ahora)
    category_labels = ['Electrónica', 'Hogar', 'Moda', 'Deportes', 'Juguetes', 'Otros']
    category_data = [25, 20, 15, 15, 10, 15]
    
    return chart_labels, chart_data, category_labels, category_data

def generate_dashboard():
    """Genera el archivo HTML del dashboard"""
    
    print("🔍 Verificando estructura de base de datos...")
    columns = check_database_structure()
    
    if not columns:
        print("❌ No se pudo verificar la estructura de la BD")
    
    print("\n📊 Obteniendo estadísticas...")
    stats = get_database_stats()
    if not stats:
        stats = {
            'total_offers': 0,
            'offers_today': 0,
            'avg_discount': 0,
            'avg_price': 0,
            'affiliate_ratio': 0,
            'cache_count': 0,
            'hourly_rate': 0,
            'uptime': 0,
            'success_rate': 0,
            'cache_size': 0
        }
    
    print("🔥 Obteniendo mejores descuentos...")
    top_discounts = get_top_discounts()
    
    print("⏰ Obteniendo ofertas recientes...")
    recent = get_recent_offers()
    
    print("📈 Generando datos de gráficas...")
    chart_labels, chart_data, category_labels, category_data = get_chart_data()
    
    # HTML del dashboard
    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromoAdictos - Dashboard Analytics</title>
    <meta http-equiv="refresh" content="30">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #6366f1;
            --secondary: #06b6d4;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1f2937;
            --gray: #6b7280;
            --light: #f3f4f6;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        h1 {
            color: var(--dark);
            font-size: 2.2em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: var(--gray);
            font-size: 1.1em;
            margin-top: 5px;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 20px;
            background: rgba(16, 185, 129, 0.1);
            border-radius: 50px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: transform 0.3s;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4em;
            margin-bottom: 15px;
        }
        
        .metric-icon.blue { background: rgba(99, 102, 241, 0.1); color: var(--primary); }
        .metric-icon.green { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .metric-icon.yellow { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
        .metric-icon.purple { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
        .metric-icon.cyan { background: rgba(6, 182, 212, 0.1); color: var(--secondary); }
        .metric-icon.red { background: rgba(239, 68, 68, 0.1); color: var(--danger); }
        
        .metric-label {
            color: var(--gray);
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .metric-value {
            color: var(--dark);
            font-size: 2em;
            font-weight: 800;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        .chart-title {
            color: var(--dark);
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 20px;
        }
        
        .chart-container {
            position: relative;
            height: 250px !important;
            width: 100%;
        }
        
        .chart-container canvas {
            max-height: 250px !important;
        }
        
        .tables-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .table-card {
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        
        .table-header {
            padding: 20px 25px;
            border-bottom: 2px solid var(--light);
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(6, 182, 212, 0.05));
        }
        
        .table-title {
            color: var(--dark);
            font-size: 1.2em;
            font-weight: 700;
        }
        
        .table-row {
            padding: 15px 25px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            transition: background 0.2s;
        }
        
        .table-row:hover {
            background: rgba(99, 102, 241, 0.03);
        }
        
        .offer-title {
            color: var(--dark);
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .offer-meta {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
        }
        
        .badge-discount { background: rgba(239, 68, 68, 0.1); color: var(--danger); }
        .badge-price { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .badge-time { background: rgba(107, 114, 128, 0.1); color: var(--gray); }
        
        @media (max-width: 768px) {
            .charts-grid, .tables-grid {
                grid-template-columns: 1fr;
            }
            .header-content {
                flex-direction: column;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-content">
                <div>
                    <h1>📊 PromoAdictos Analytics</h1>
                    <p class="subtitle">Dashboard de Monitoreo en Tiempo Real</p>
                </div>
                <div class="status">
                    <div class="status-dot"></div>
                    <span>Sistema Activo</span>
                </div>
            </div>
        </header>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-icon blue"><i class="fas fa-shopping-bag"></i></div>
                <div class="metric-label">Total Publicadas</div>
                <div class="metric-value">''' + str(stats.get('total_offers', 0)) + '''</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon green"><i class="fas fa-calendar-day"></i></div>
                <div class="metric-label">Ofertas Hoy</div>
                <div class="metric-value">''' + str(stats.get('offers_today', 0)) + '''</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon yellow"><i class="fas fa-percentage"></i></div>
                <div class="metric-label">Descuento Promedio</div>
                <div class="metric-value">''' + str(stats.get('avg_discount', 0)) + '''%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon purple"><i class="fas fa-dollar-sign"></i></div>
                <div class="metric-label">Precio Promedio</div>
                <div class="metric-value">$''' + "{:,.0f}".format(stats.get('avg_price', 0)) + '''</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon cyan"><i class="fas fa-link"></i></div>
                <div class="metric-label">Links Afiliado</div>
                <div class="metric-value">''' + str(stats.get('affiliate_ratio', 0)) + '''%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-icon red"><i class="fas fa-database"></i></div>
                <div class="metric-label">En Caché</div>
                <div class="metric-value">''' + "{:,}".format(stats.get('cache_count', 0)) + '''</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3 class="chart-title">📈 Tendencia Semanal</h3>
                <div class="chart-container">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h3 class="chart-title">🏷️ Categorías</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="tables-grid">
            <div class="table-card">
                <div class="table-header">
                    <h3 class="table-title">🔥 Mejores Descuentos</h3>
                </div>
                <div class="table-body">'''
    
    # Agregar ofertas con mejor descuento
    if top_discounts:
        for offer in top_discounts[:5]:
            html += f'''
                    <div class="table-row">
                        <div class="offer-title">{str(offer.get('title', 'Sin título'))[:80]}...</div>
                        <div class="offer-meta">
                            <span class="badge badge-discount">{offer.get('discount_pct', 0)}% OFF</span>
                            <span class="badge badge-price">${offer.get('price_final', 0):,.0f}</span>
                        </div>
                    </div>'''
    else:
        html += '''
                    <div class="table-row">
                        <div class="offer-title">No hay ofertas disponibles aún</div>
                    </div>'''
    
    html += '''
                </div>
            </div>
            
            <div class="table-card">
                <div class="table-header">
                    <h3 class="table-title">⏰ Últimas Publicadas</h3>
                </div>
                <div class="table-body">'''
    
    # Agregar ofertas recientes
    if recent:
        for offer in recent[:5]:
            html += f'''
                    <div class="table-row">
                        <div class="offer-title">{str(offer.get('title', 'Sin título'))[:80]}...</div>
                        <div class="offer-meta">
                            <span class="badge badge-discount">{offer.get('discount_pct', 0)}% OFF</span>
                            <span class="badge badge-time">{offer.get('time_ago', 'Reciente')}</span>
                        </div>
                    </div>'''
    else:
        html += '''
                    <div class="table-row">
                        <div class="offer-title">No hay ofertas recientes</div>
                    </div>'''
    
    html += '''
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Configuración para mantener el tamaño fijo
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.responsive = true;
        
        // Gráfica de tendencia
        const ctx1 = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx1, {
            type: 'line',
            data: {
                labels: ''' + json.dumps(chart_labels) + ''',
                datasets: [{
                    label: 'Ofertas',
                    data: ''' + json.dumps(chart_data) + ''',
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: { 
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        
        // Gráfica de categorías
        const ctx2 = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: ''' + json.dumps(category_labels) + ''',
                datasets: [{
                    data: ''' + json.dumps(category_data) + ''',
                    backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            padding: 8,
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>'''
    
    # Guardar archivo
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Dashboard generado exitosamente: {DASHBOARD_PATH}")
    print(f"📊 Estadísticas: {stats.get('total_offers', 0)} ofertas totales, {stats.get('offers_today', 0)} hoy")

if __name__ == "__main__":
    generate_dashboard()