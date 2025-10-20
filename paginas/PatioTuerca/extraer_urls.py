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

#Función para extraer los urls de los vehiculos de un solo año
def extraer_vehiculos_por_anio(anio, num_paginas=3, pausa=2):
    """Versión ultra-simplificada - extrae vehículos de un año específico"""
    todas_urls = []
    base_url = f"{URL_BASE}/-/-/-/{anio}"
    
    print(f"🚗 Buscando vehículos del año {anio}...")
    
    for pagina in range(1, num_paginas + 1):
        if pagina == 1:
            url_pagina = base_url
        else:
            codigo = generar_codigo_base64(pagina - 1)
            url_pagina = f"{base_url}?page={codigo}"
        
        print(f"🔎 Página {pagina}: {url_pagina}")
        
        try:
            urls = extraer_urls_vehiculos(url_pagina)
            if not urls:
                print(f"⚠️ No hay más resultados para {anio}")
                break
            
            todas_urls.extend(urls)
            print(f"✅ {len(urls)} vehículos encontrados")
            time.sleep(pausa)
            
        except Exception as e:
            print(f"❌ Error en página {pagina}: {e}")
            break
    
    print(f"📊 Total para {anio}: {len(todas_urls)} vehículos")
    return todas_urls

#Función para extraer los vehículos de varios años usando el de un solo año
def extraer_multiples_anios(anios, num_paginas=3, pausa=2):
    """Extrae vehículos de múltiples años"""
    if isinstance(anios, int):
        anios = [anios]
    
    resultados = {}
    
    for anio in anios:
        print(f"\n{'='*40}")
        urls = extraer_vehiculos_por_anio(anio, num_paginas, pausa)
        resultados[anio] = urls
        time.sleep(pausa * 2)  # Pausa más larga entre años
    
    return resultados

    # Ejemplo 2: Múltiples años
    print("\n📅 EJEMPLO 2: Múltiples años")
    anios_a_buscar = [2023, 2022, 2021]
    resultados = extraer_multiples_anios(anios_a_buscar, num_paginas=2)