import requests

def buscar_con_token(busqueda, access_token):
    url = "https://api.mercadolibre.com/sites/MLM/search"
    
    # AQUÍ ESTÁ LA CLAVE: Autenticación Bearer
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        'q': busqueda,
        'sort': 'price_asc',
        'limit': 5
    }

    print(f"📡 Buscando '{busqueda}' con credenciales...")

    try:
        response = requests.get(url, headers=headers, params=params)
        
        # Si el token venció o está mal, lanzará error aquí
        response.raise_for_status() 
        
        data = response.json()
        items = data.get('results', [])
        
        if not items:
            print("⚠️ No se encontraron resultados (o la búsqueda no trajo nada).")
            return

        print(f"✅ ¡Éxito! Encontrados {len(items)} items:\n")
        
        for item in items:
            precio = item.get('price')
            titulo = item.get('title')
            link = item.get('permalink')
            print(f"💰 ${precio} | {titulo}")
            print(f"🔗 {link}\n")

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error de Permisos: {e}")
        print(f"Mensaje API: {response.text}")
        print("💡 TIP: ¿Es posible que tu token haya caducado? Duran 6 horas.")

if __name__ == "__main__":
    # PEGA AQUÍ TU TOKEN (El que copiaste en el Paso 2)
    MI_TOKEN = "PEGA_TU_TOKEN_AQUI_DENTRO_DE_LAS_COMILLAS"
    
    if MI_TOKEN == "PEGA_TU_TOKEN_AQUI_DENTRO_DE_LAS_COMILLAS":
        print("¡OJO! Te falta pegar el token en la variable MI_TOKEN en el código.")
    else:
        buscar_con_token("nintendo switch oled", MI_TOKEN)