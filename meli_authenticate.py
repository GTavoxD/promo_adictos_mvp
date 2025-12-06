import requests
import webbrowser

CLIENT_ID = "2166638248390526"
CLIENT_SECRET = "j3RacEkZgAjisE6LVTPbvTsQaYgnh3Do"
REDIRECT_URI = "https://www.google.com"

# 1. Abre esta URL para autorizar la app manualmente
auth_url = f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
print("Abriendo navegador para autorizar...")
webbrowser.open(auth_url)

# 2. Luego de login, copiarás el `code` que aparece en la URL y lo pegas acá:
auth_code = input("Pega el código 'code' de la URL después del login: ")

# 3. Intercambio del code por un token
response = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": auth_code,
    "redirect_uri": REDIRECT_URI
})

data = response.json()
print("ACCESS TOKEN:\n", data["access_token"])
print("REFRESH TOKEN:\n", data["refresh_token"])
