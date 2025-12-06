import os
import requests
from dotenv import load_dotenv, set_key

# Cargar variables del archivo .env
env_file = ".env"
load_dotenv(env_file)

def refrescar_credenciales():
    """
    Renueva el token y actualiza el .env
    """
    # Limpiamos comillas por si acaso quedaron en el .env
    client_id = os.getenv("MELI_CLIENT_ID", "").strip().strip("'").strip('"')
    client_secret = os.getenv("MELI_CLIENT_SECRET", "").strip().strip("'").strip('"')
    refresh_token = os.getenv("MELI_REFRESH_TOKEN", "").strip().strip("'").strip('"')

    if not all([client_id, client_secret, refresh_token]):
        print("❌ Error: Faltan variables en el archivo .env")
        return None

    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }

    print("🔄 Renovando tokens con MercadoLibre...")
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        data = response.json()

        # --- AQUÍ ESTABA EL ERROR: Faltaba definir estas variables ---
        new_access_token = data['access_token']
        new_refresh_token = data['refresh_token']
        # -------------------------------------------------------------

        # Guardamos el nuevo refresh token en el .env para la próxima
        print("💾 Guardando nuevo Refresh Token en .env...")
        set_key(env_file, "MELI_REFRESH_TOKEN", new_refresh_token, quote_mode="never")
        
        # Recargamos para asegurar que memoria y archivo estén sincronizados
        load_dotenv(env_file, override=True)
        
        return new_access_token

    except requests.exceptions.HTTPError as e:
        print(f"❌ Error al renovar token: {e}")
        print(f"Respuesta API: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def buscar_ofertas(query, access_token):
    url = "https://api.mercadolibre.com/sites/MLM/search"
    
    # ESTRATEGIA: "HONEST BOT"
    # 1. Usamos el Token (para demostrar que somos devs registrados).
    # 2. En User-Agent ponemos el nombre de tu App (definido en el panel de ML).
    #    Esto le dice a ML: "Soy yo, la app que registraste, no soy un hacker".
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "PromoAdictosBot/1.0",  # <--- Nombre honesto
        "Accept": "application/json"
    }
    
    params = {
        "q": query,
        "sort": "price_asc",
        "limit": 5
    }

    print(f"📡 Buscando: '{query}' (Modo App Honesta)...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # Si falla, vamos a imprimir el error PERO NO nos rendimos
        if response.status_code != 200:
            print(f"❌ Error {response.status_code} en búsqueda.")
            # Intento de rescate: Imprimir si el token sirve para OTROS datos
            # Esto nos dirá si el bloqueo es SOLO en búsqueda
            print("   (El firewall de búsqueda está agresivo hoy)")
            return []
            
        results = response.json().get('results', [])
        return results

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return []


# --- Flujo Principal ---
if __name__ == "__main__":
    # 1. Obtener un token válido
    token_valido = refrescar_credenciales()

    if token_valido:
        # 2. Usar el token para buscar
        productos = buscar_ofertas("Nintendo Switch", token_valido)

        if productos:
            print("\n✅ ¡ÉXITO ROTUNDO! Resultados encontrados:")
            print("-----------------------")
            for p in productos:
                precio = p.get('price')
                titulo = p.get('title')
                link = p.get('permalink')
                print(f"💰 ${precio} | {titulo}")
                print(f"🔗 {link}\n")
        else:
            print("⚠️ La búsqueda funcionó, pero no trajo resultados (o hubo un bloqueo silencioso).")
    else:
        print("No se pudo proceder con la búsqueda.")
# ... después del bloque de búsqueda ...
    
    # --- PRUEBA DE RESPALDO: LEER UN ITEM ESPECÍFICO ---
    # Si esto funciona, tu proyecto ESTÁ VIVO, solo que la búsqueda general falla.
    print("\n🧪 Test de Lectura Directa (Item específico)...")
    id_prueba = "MLM1909062337" # Un item real de ejemplo (puede variar)
    url_item = f"https://api.mercadolibre.com/items/{id_prueba}"
    headers_item = {"Authorization": f"Bearer {token_valido}"}
    
    resp_item = requests.get(url_item, headers=headers_item)
    if resp_item.status_code == 200:
        d = resp_item.json()
        print(f"✅ ¡LECTURA EXITOSA! {d.get('title')} cuesta ${d.get('price')}")
        print("💡 Conclusión: Tienes acceso a DATOS, pero el buscador (/search) es estricto.")
    else:
        print(f"❌ Falló lectura de item: {resp_item.status_code}")