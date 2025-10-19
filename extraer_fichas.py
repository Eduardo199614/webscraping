import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

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


def extraer_id(soup, url):
    """Extrae el ID del vehículo desde el meta tag o la URL."""
    meta_id = soup.find("meta", {"itemprop": "productID"})
    if meta_id and meta_id.get("content"):
        return meta_id["content"]

    # Alternativa: extraer desde la URL (últimos números)
    import re
    match = re.search(r"/(\d+)$", url)
    return match.group(1) if match else None


def extraer_ficha_tecnica(url):
    """Extrae ficha técnica y summary, con ID, fecha y estado inicial."""
    inicio = time.time()
    mensaje = ""
    ejecucion_exitosa = True

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {
            "ID": None,
            "FechaIngreso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Vigencia": "No activo",
            "Data": {},
            "mensaje": f"Error al acceder a {url}: {e}",
            "TiempoEjecucion": 0,
            "ejecucion": False
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # 1️⃣ ID y fecha
    id_auto = extraer_id(soup, url)
    fecha_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2️⃣ Datos del summary
    data_summary = extraer_summary(soup)

    # 3️⃣ Datos técnicos
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
    else:
        print("No se encontró una ficha válida.")
    # 4️⃣ Campos de interés
    campos = ["Año", "Precio", "Marca", "Modelo", "Kilometraje", "Motor(cilindraje)", "Transmisión"]
    data_final = {} 
    for campo in campos: 
        data_final[campo] = data_summary.get(campo) or data_technical.get(campo) or None

    # 5️⃣ Validación
    faltantes = [k for k, v in data_final.items() if not v]
    if faltantes:
        mensaje = f"No se pudo obtener: {', '.join(faltantes)}"
        ejecucion_exitosa = False
    else:
        mensaje = "Datos obtenidos correctamente"

    tiempo_total = round(time.time() - inicio, 3)

    return {
        "ID": id_auto,
        "FechaIngreso": fecha_ingreso,
        "Vigencia": "Activo",
        "Data": data_final,
        "mensaje": mensaje,
        "TiempoEjecucion": tiempo_total,
        "ejecucion": ejecucion_exitosa
    }


def extraer_fichas_desde_lista(urls, pausa=3):
    """Procesa una lista de URLs y devuelve los resultados (sin guardar aún)."""
    resultados = []

    for i, url in enumerate(urls, start=1):
        print(f"({i}/{len(urls)}) 🔍 Extrayendo datos de: {url}")
        resultado = extraer_ficha_tecnica(url)
        resultados.append(resultado)
        print(f"✅ {resultado['mensaje']}\n")
        time.sleep(pausa)
    return resultados


if __name__ == "__main__":
    test_url = "https://ecuador.patiotuerca.com/vehicle/autos-kia-k3_x-line-guayaquil-2025/1935036"
    resultado = extraer_ficha_tecnica(test_url)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
