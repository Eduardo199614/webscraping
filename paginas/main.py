import requests
from bs4 import BeautifulSoup
import json
import base64
import time

URL_BASE = "https://ecuador.patiotuerca.com/usados/-/autos"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extraer_urls_vehiculos(url):
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
    """Convierte un número entero (1, 2, 3, ...) a su representación Base64 (MQ==, Mg==, ...)"""
    return base64.b64encode(str(numero).encode()).decode()


def extraer_todas_las_paginas(num_paginas=5, pausa=2):
    """Extrae URLs desde la página 1 y las siguientes, generando el código base64 a partir de la página 2"""
    todas_urls = []

    for i in range(1, num_paginas + 1):
        if i == 1:
            url_pagina = URL_BASE  # Página 1
        else:
            codigo = generar_codigo_base64(i - 1)  # MQ== corresponde a página 2
            url_pagina = f"{URL_BASE}?page={codigo}"

        print(f"🔎 Extrayendo página {i} → {url_pagina}")

        urls = extraer_urls_vehiculos(url_pagina)
        if not urls:
            print("⚠️ No se encontraron más resultados, deteniendo.")
            break

        todas_urls.extend(urls)
        print(f"✅ {len(urls)} vehículos encontrados en la página {i}\n")
        time.sleep(pausa)  # Pausa entre solicitudes

    return todas_urls


# Ejecutar scraping (por ejemplo, primeras 5 páginas)
todas = extraer_todas_las_paginas(num_paginas=5)

print(f"\n🔹 Total de URLs encontradas: {len(todas)}")
for u in todas[:10]:
    print("➡️", u)