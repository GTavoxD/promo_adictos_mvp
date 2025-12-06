import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import Counter

import sys
sys.path.append("src")
from filters import BANNED_KEYWORDS

OUTPUT_DIR = "dashboard/analytics"
os.makedirs(OUTPUT_DIR, exist_ok=True)
csv_path = "data/bloqueados.csv"

# Verificación robusta del archivo antes de intentar leerlo
if not os.path.exists(csv_path):
    print("❌ El archivo bloqueados.csv no existe.")
    exit()

# Verifica si el archivo tiene encabezados
with open(csv_path, "r", encoding="utf-8") as f:
    header = f.readline().strip()
    if not header:
        print("⚠️ El archivo está vacío (sin encabezados).")
        exit()

# Si pasa todas las verificaciones, ahora sí lee el CSV
df = pd.read_csv(csv_path)


def generate_blocked_reasons_chart(csv_path="data/bloqueados.csv"):
    df = pd.read_csv(csv_path)
    
    all_reasons = []
    for title in df["title"].fillna(""):
        title_lower = title.lower()
        for word in BANNED_KEYWORDS:
            if word in title_lower:
                all_reasons.append(word)

    reason_counts = Counter(all_reasons)
    common_reasons = dict(reason_counts.most_common(10))

    if not common_reasons:
        print("No hay razones comunes de bloqueo para graficar.")
        return

    plt.figure(figsize=(10, 5))
    plt.barh(list(common_reasons.keys())[::-1], list(common_reasons.values())[::-1])
    plt.title("Motivos de Bloqueo Más Comunes")
    plt.xlabel("Cantidad de productos bloqueados")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/blocked_reasons.png")
    plt.close()

    print("✅ Gráfico de bloqueos generado en", f"{OUTPUT_DIR}/blocked_reasons.png")

# NOTA: Asegúrate de importar o definir BANNED_KEYWORDS en este script o pásalos como parámetro

if __name__ == "__main__":
    from dashboard_generator import load_data
    from filters import BANNED_KEYWORDS

    generate_blocked_reasons_chart()
