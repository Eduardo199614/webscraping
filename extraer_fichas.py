# extraer_fichas.py
import requests
from bs4 import BeautifulSoup
import json
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

def extraer_summary(soup):
    """Extrae los datos básicos desde la sección #summary."""
    resumen = {}
    section = soup.find("section", {"id": "summary"})
    if not section:
        return resumen

    for div in section.find_all("div", class_="col"):
        small_tag = div.find("small")
        if not small_tag:
            continue

        nombre = small_tag.get_text(strip=True)
        valor = div.get_text(strip=True).replace(nombre, "").strip()

        # Estandarizar claves conocidas
        if "Año" in nombre:
            resumen["Año"] = valor
        elif "Recorrido" in nombre or "Kilometraje" in nombre:
            resumen["Kilometraje"] = valor
        elif "Precio" in nombre:
            resumen["Precio"] = valor
        elif "Ciudad" in nombre:
            resumen["Ciudad"] = valor
        elif "Pago" in nombre:
            resumen["TipoPago"] = valor

    return resumen


def extraer_ficha_tecnica(url):
    """Extrae ficha técnica y summary, priorizando summary si hay datos duplicados."""
    inicio = time.time()
    mensaje = ""
    ejecucion_exitosa = True

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {
            "Data": [],
            "mensaje": f"Error al acceder a {url}: {e}",
            "TiempoEjecucion": 0,
            "ejecucion": False
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # 1️⃣ Datos del summary
    data_summary = extraer_summary(soup)

    # 2️⃣ Datos técnicos (ficha técnica)
    data_technical = {}
    ficha = soup.find("section", {"id": "technicalData"})
    if ficha:
        for p in ficha.find_all("p", class_="m-none"):
            nombre_tag = p.find("small")
            valor_tag = p.find("span")
            if nombre_tag and valor_tag:
                clave = nombre_tag.get_text(strip=True)
                valor = valor_tag.get_text(strip=True)
                data_technical[clave] = valor

    # 3️⃣ Combinamos ambos (summary tiene prioridad)
    campos = ["Año", "Precio", "Marca", "Modelo", "Kilometraje", "Motor(cilindraje)", "Transmisión"]
    data_final = {}
    for campo in campos:
        data_final[campo] = data_summary.get(campo) or data_technical.get(campo) or None

    # 4️⃣ Mensaje en caso de campos faltantes
    faltantes = [k for k, v in data_final.items() if not v]
    if faltantes:
        mensaje = f"No se pudo obtener: {', '.join(faltantes)}"
        ejecucion_exitosa = False
    else:
        mensaje = "Datos obtenidos correctamente"

    tiempo_total = round(time.time() - inicio, 3)

    return {
        "Data": [data_final],
        "mensaje": mensaje,
        "TiempoEjecucion": tiempo_total,
        "ejecucion": ejecucion_exitosa
    }


def extraer_fichas_desde_lista(urls, pausa=3, salida_json="fichas_autos.json"):
    """Procesa una lista de URLs y guarda el resultado en JSON."""
    resultados = []

    for i, url in enumerate(urls, start=1):
        print(f"({i}/{len(urls)}) 🔍 Extrayendo datos de: {url}")
        resultado = extraer_ficha_tecnica(url)
        resultados.append(resultado)
        print(f"✅ {resultado['mensaje']}\n")
        time.sleep(pausa)

    with open(salida_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Se guardaron {len(resultados)} resultados en '{salida_json}'")
    return resultados


if __name__ == "__main__":
    # Ejemplo individual
    test_url = "https://ecuador.patiotuerca.com/vehicle/autos-kia-k3_x-line-guayaquil-2025/1935036"
    resultado = extraer_ficha_tecnica(test_url)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
