import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import webbrowser  # 👈 IMPORTAR AQUÍ
from bloqueos_dashboard import generate_blocked_reasons_chart  # 👈 asegurar que exista y funcione

OUTPUT_DIR = "dashboard/analytics"
HTML_PATH = "dashboard/index.html"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv("data/ofertas_publicadas.csv")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def plot_discount_histogram(df):
    if "discount_pct" not in df.columns:
        print("[DASHBOARD] ⚠️ No hay columna 'discount_pct' en el archivo. Saltando histograma.")
        return
    sns.histplot(df["discount_pct"], bins=20, kde=False)
    plt.title("Distribución de Descuentos (%)")
    plt.xlabel("Descuento (%)")
    plt.ylabel("Cantidad de Ofertas")
    plt.savefig("dashboard/analytics/discount_histogram.png")
    plt.close()


def plot_price_ranges(df):
    bins = [0, 999, 4999, 9999, float("inf")]
    labels = ["$0–$999", "$1,000–$4,999", "$5,000–$9,999", "$10,000+"]
    df["price_range"] = pd.cut(df["price"], bins=bins, labels=labels)
    plt.figure(figsize=(8, 5))
    df["price_range"].value_counts().reindex(labels).plot(kind="bar")
    plt.title("Rango de precios publicados")
    plt.ylabel("Cantidad")
    plt.xlabel("Rango de Precio")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/price_ranges.png")
    plt.close()

def plot_publications_by_day(df):
    df["day"] = df["timestamp"].dt.date
    pub_per_day = df.groupby("day").size()
    plt.figure(figsize=(10, 4))
    pub_per_day.plot()
    plt.title("Ofertas publicadas por día")
    plt.ylabel("Cantidad")
    plt.xlabel("Fecha")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/publications_per_day.png")
    plt.close()

def generate_dashboard():
    df = load_data()
    plot_discount_histogram(df)
    plot_price_ranges(df)
    plot_publications_by_day(df)
    generate_blocked_reasons_chart()  # 👈 genera el gráfico extra

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>📊 Dashboard PromoAdictos</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f9f9f9;
        }}
        h1 {{
            color: #333;
        }}
        img {{
            max-width: 100%;
            margin-bottom: 30px;
            border: 1px solid #ccc;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>📊 Dashboard PromoAdictos</h1>
    <p>Actualizado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <h2>Distribución de Descuentos</h2>
    <img src="analytics/discount_distribution.png" alt="Distribución de Descuentos">

    <h2>Rango de Precios</h2>
    <img src="analytics/price_ranges.png" alt="Rangos de Precios">

    <h2>Ofertas Publicadas por Día</h2>
    <img src="analytics/publications_per_day.png" alt="Publicaciones por Día">

    <h2>🛑 Razones de Bloqueo</h2>
    <img src="analytics/blocked_reasons.png" alt="Razones de Bloqueo">
</body>
</html>""")

    print("✅ Dashboard generado en", HTML_PATH)
    webbrowser.open(f"file://{os.path.abspath(HTML_PATH)}")

if __name__ == "__main__":
    generate_dashboard()
