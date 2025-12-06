import requests
import json

def buscar_ofertas_ml(query, limite=10):
    # MLM = MercadoLibre México
    url = f"https://api.mercadolibre.com/sites/MLM/search"
    
    params = {
        'q': query,
        'limit': limite,
        'sort': 'price_asc', # Opcional: ordenar por precio
        # 'condition': 'new' # Opcional: solo productos nuevos
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Lanza error si falla la petición
        data = response.json()

        ofertas = []
        
        # Iteramos sobre los resultados
        for item in data.get('results', []):
            producto = {
                'id': item.get('id'),
                'titulo': item.get('title'),
                'precio': item.get('price'),
                'moneda': item.get('currency_id'),
                'link': item.get('permalink'),
                'imagen': item.get('thumbnail'),
                'envio_gratis': item.get('shipping', {}).get('free_shipping', False)
            }
            ofertas.append(producto)
            
        return ofertas

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API: {e}")
        return []

# --- Prueba del script ---
if __name__ == "__main__":
    busqueda = "Laptop Gamer"
    resultados = buscar_ofertas_ml(busqueda)
    
    print(f"Encontrados {len(resultados)} resultados para '{busqueda}':")
    for p in resultados:
        print(f"- {p['titulo']} | ${p['precio']} MXN | {p['link']}")