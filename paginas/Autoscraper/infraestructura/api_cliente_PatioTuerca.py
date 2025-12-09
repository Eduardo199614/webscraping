from __future__ import annotations
from typing import Protocol, Dict, Any, List
from bs4 import BeautifulSoup
from paginas.Autoscraper.dominio.modelo import Vehiculo
import requests
import re
import time, base64, json

URL_BASE = "https://ecuador.patiotuerca.com/usados/-/autos"

#-------------------------Web-----------------------------------
class WebClient(Protocol):
    def fetch_html(self, url: str) -> str: ...

class RequestsWebClient(WebClient):
    def __init__(self, user_agent: str, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def fetch_html(self, url: str) -> str:
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

#---------------------------Extracción de las urls para sacar data---------------------------
def generar_codigo_base64(n: int) -> str:
    """Codifica un número de página en base64, como usa PatioTuerca."""
    return base64.b64encode(str(n).encode()).decode()


class PatioTuercaRepositorio():
    """Repositorio que obtiene vehículos por año desde PatioTuerca."""
    def __init__(self, web_client: RequestsWebClient, pausa: int = 5, num_paginas: int = 10): #modificar la cantidad de páginas o el tiempo de pausa aquí de ser necesario.
        self.web = web_client
        self.num_paginas = num_paginas
        self.pausa = pausa

    def _extraer_urls_vehiculos(self, url_pagina: str) -> List[str]:
        """Extrae URLs de fichas de vehículos a partir del JSON-LD embebido en la página."""
        html = self.web.fetch_html(url_pagina)
        soup = BeautifulSoup(html, "html.parser")

        urls = []
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string)
                # Algunos scripts tienen una lista de objetos, otros un dict
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "Car" and "url" in item:
                            urls.append(item["url"])
                elif isinstance(data, dict):
                    if data.get("@type") == "Car" and "url" in data:
                        urls.append(data["url"])
            except Exception:
                continue

        return urls

    def obtener_vehiculos_por_anio(self, anio: int) -> List[Vehiculo]:
        """Recorre las páginas de resultados para un año específico y extrae las fichas completas."""
        print(f"🚗 Buscando vehículos del año {anio}...")
        base_url = f"{URL_BASE}/-/-/-/{anio}"
        todas_urls = []

        for pagina in range(1, self.num_paginas + 1):
            # Construye la URL de la página actual
            if pagina == 1:
                url_pagina = base_url
            else:
                codigo = generar_codigo_base64(pagina - 1)
                url_pagina = f"{base_url}?page={codigo}"

            print(f"🔎 Página {pagina}: {url_pagina}")
            try:
                urls = self._extraer_urls_vehiculos(url_pagina)
                if not urls:
                    print(f"⚠️ No hay más resultados para {anio}")
                    break
                todas_urls.extend(urls)
                print(f"✅ {len(urls)} URLs encontradas en página {pagina}")
                time.sleep(self.pausa)
            except Exception as e:
                print(f"❌ Error en página {pagina}: {e}")
                break

        # Extrae las fichas completas de cada URL
        vehiculos = []
        for i, url in enumerate(todas_urls, start=1):
            try:
                html = self.web.fetch_html(url)
                ficha = FichaExtractor.parsear_html(html, url)
                if not ficha["id"]:
                    continue
                vehiculos.append(Vehiculo(
                id=ficha["id"],
                summary=ficha["summary"],
                ficha_tecnica=ficha["ficha_tecnica"],
                url = ficha["url"]
                ))
                print(f"   🔹 {i}/{len(todas_urls)}: {ficha['id']} OK")
                time.sleep(0.8)
            except Exception as e:
                print(f"   ⚠️ Error al procesar {url}: {e}")

        print(f"📊 Total extraídos para {anio}: {len(vehiculos)} vehículos")
        return vehiculos


#--------------------Extracción de la Data------------------------
class FichaExtractor:
    @staticmethod
    def extraer_id(soup: BeautifulSoup, url: str) -> str | None:
        meta_id = soup.find("meta", {"itemprop": "productID"})
        if meta_id and meta_id.get("content"):
            return meta_id["content"]

        match = re.search(r"/(\d+)$", url)
        return match.group(1) if match else None

    @staticmethod
    def extraer_summary(soup: BeautifulSoup) -> Dict[str, Any]:
        data = {}
        section = soup.find("section", id="summary")
        if not section:
            return data

        for div in section.find_all("div", class_="col"):
            small = div.find("small")
            if not small:
                continue
            nombre = small.get_text(strip=True)
            valor = div.get_text(strip=True).replace(nombre, "").strip()
            data[nombre] = valor
        return data

    @staticmethod
    def extraer_ficha_tecnica(soup: BeautifulSoup) -> Dict[str, Any]:
        data = {}
        ficha = soup.find("section", id="technicalData")
        if not ficha:
            return data
        
        for p in ficha.find_all("p", class_="m-none"):
            nombre = p.find("small")
            valor = p.find("span")
            if nombre and valor:
                data[nombre.get_text(strip=True)] = valor.get_text(strip=True)
        return data

    @staticmethod
    def parsear_html(html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        return {
            "id": FichaExtractor.extraer_id(soup, url),
            "summary": FichaExtractor.extraer_summary(soup),
            "ficha_tecnica": FichaExtractor.extraer_ficha_tecnica(soup),
            "url": url
        }
    
#---------------------------------Adaptador-----------------------------
class PatioTuercaClientAdapter:
    """Adaptador que expone la misma interfaz de un ApiClient estándar."""
    def __init__(self, web_client: RequestsWebClient, anios: list[int]):
        self.repo = PatioTuercaRepositorio(web_client)
        self.anios = anios

    def fetch_year(self, anio: int) -> List[Dict[str, Any]]:
        """Devuelve las fichas de vehículos de un solo año."""
        vehiculos = self.repo.obtener_vehiculos_por_anio(anio)

        entities: List[Dict[str, Any]] = []
        for v in vehiculos:
            entities.append({
                "id_record": v.id,
                "summary": v.summary,
                "ficha_tecnica": v.ficha_tecnica,
                "url": v.url
            })
        return entities

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de fichas de vehículos de todos los años indicados."""
        all_entities: List[Dict[str, Any]] = []
        for anio in self.anios:
            vehiculos = self.repo.obtener_vehiculos_por_anio(anio)
            # Convertimos los Vehiculo (dataclasses o dicts) a diccionarios simples
            for v in vehiculos:
                all_entities.append({
                    "id": v.id,
                    "summary": v.summary,
                    "ficha_tecnica": v.ficha_tecnica,
                    "url":v.url
                })
        return all_entities
