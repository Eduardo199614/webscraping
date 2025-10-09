import requests
from bs4 import BeautifulSoup
import json

URL = "https://ecuador.patiotuerca.com/usados/-/autos"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extraer_urls_vehiculos(url):
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            
            # Algunos scripts tienen listas, otros un solo objeto
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Car" and "url" in item:
                        urls.append(item["url"])
            elif data.get("@type") == "Car" and "url" in data:
                urls.append(data["url"])
        except Exception:
            continue

    return urls

# Ejecutar
urls_autos = extraer_urls_vehiculos(URL)
print(f"Encontradas {len(urls_autos)} URLs de vehículos:")
for u in urls_autos[:10]: #Cambiar esto para mostrar en el print todos los links
    print("➡️", u)