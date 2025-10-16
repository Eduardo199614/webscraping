# extraer_urls.py
import requests
from bs4 import BeautifulSoup
import json
import base64
import time

URL_BASE = "https://ecuador.patiotuerca.com/usados/-/autos"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extraer_urls_vehiculos(url):
    """Extrae URLs de vehículos desde una página dada."""
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    urls = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Car" and "url" in item:
                        urls.append(item["url"])
            elif data.get("@type") == "Car" and "url" in data:
                urls.append(data["url"])
        except Exception:
            continue
    return urls


def generar_codigo_base64(numero):
    """Convierte un número entero (1, 2, 3, ...) a su representación Base64."""
    return base64.b64encode(str(numero).encode()).decode()


def extraer_todas_las_paginas(num_paginas=5, pausa=2):
    """Extrae URLs de múltiples páginas de resultados."""
    todas_urls = []

    for i in range(1, num_paginas + 1):
        if i == 1:
            url_pagina = URL_BASE
        else:
            codigo = generar_codigo_base64(i - 1)
            url_pagina = f"{URL_BASE}?page={codigo}"

        print(f"🔎 Extrayendo página {i} → {url_pagina}")
        urls = extraer_urls_vehiculos(url_pagina)

        if not urls:
            print("⚠️ No se encontraron más resultados, deteniendo.")
            break

        todas_urls.extend(urls)
        print(f"✅ {len(urls)} vehículos encontrados en la página {i}\n")
        time.sleep(pausa)

    return todas_urls


if __name__ == "__main__":
    # Prueba rápida
    todas = extraer_todas_las_paginas(num_paginas=3)
    print(f"\n🔹 Total de URLs encontradas: {len(todas)}")
    for u in todas[:10]:
        print("➡️", u)
