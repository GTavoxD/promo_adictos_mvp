import requests

CLIENT_ID = "2166638248390526"
CLIENT_SECRET = "j3RacEkZgAjisE6LVTPbvTsQaYgnh3Do"
REDIRECT_URI = "https://www.google.com"
AUTHORIZATION_CODE = "TG-692fef594696be0001b8b512-52573057"

response = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": AUTHORIZATION_CODE,
    "redirect_uri": REDIRECT_URI
})

data = response.json()

print("ACCESS TOKEN:", data.get("access_token"))
print("REFRESH TOKEN:", data.get("refresh_token"))
print("EXPIRES IN (secs):", data.get("expires_in"))
