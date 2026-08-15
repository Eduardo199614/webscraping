from __future__ import annotations
from typing import Protocol, Dict, Any, List
from bs4 import BeautifulSoup
from paginas.Autoscraper.dominio.modelo import Vehiculo
import requests
import re
import time, base64, json
from urllib.parse import urljoin
URL_BASE = ["https://ecuador.patiotuerca.com/usados/-/autos",
            "https://ecuador.patiotuerca.com/usados/-/pesados"]
 
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
"""def generar_codigo_base64(n: int) -> str:
    #Codifica un número de página en base64, como usa PatioTuerca.
    return base64.b64encode(str(n).encode()).decode()"""

#Actualmente ya no se usa esto
 
 
class PatioTuercaRepositorio():
    """Repositorio que obtiene vehículos por año desde PatioTuerca."""

    def __init__(self, web_client: RequestsWebClient, pausa: int = 2, num_paginas: int = 300): #modificar la cantidad de páginas o el tiempo de pausa aquí de ser necesario.

        self.web = web_client
        self.num_paginas = num_paginas
        self.pausa = pausa
 
    def _extraer_urls_vehiculos(self, url_pagina: str) -> List[str]:
        #Extrae las URLs de todos los vehículos presentes en la página.

        html = self.web.fetch_html(url_pagina)
        soup = BeautifulSoup(html, "html.parser")

        base_url = "https://ecuador.patiotuerca.com"

        urls = set()

        for a in soup.select('a[href^="/vehicle/"]'):
            href = a.get("href")
            if href:
                urls.add(urljoin(base_url, href))

        return sorted(urls)
 
    def obtener_vehiculos_por_anio(self, anio: int) -> List[Vehiculo]:
        """Recorre las páginas de resultados para un año específico y extrae las fichas completas."""
        todas_urls = [] #almacenar todas las urls
        for i in URL_BASE:
            print(f"🚗 Buscando vehículos del año {anio} de la url base: {i}")
            base_url = f"{i}?year_min={anio}&year_max={anio}"
            base_url_pagina = i
            for pagina in range(1, self.num_paginas + 1):
                # Construye la URL de la página actual
                if pagina == 1:
                    url_pagina = base_url
                else:
                    url_pagina = f"{base_url_pagina}?page={pagina}&year_min=2015&year_max=2015"
 
                print(f"🔎 Página {pagina}: {url_pagina}")
                try:
                    urls = self._extraer_urls_vehiculos(url_pagina)
                    if len(urls) <= 3:
                        print(f"⚠️ No hay más resultados para {anio}")
                        break
                    todas_urls.extend(urls)
                    print(f"✅ {len(urls)} URLs encontradas en página {pagina}")
                    time.sleep(self.pausa)
                except Exception as e:
                    print(f"❌ Error en página {pagina}: {e}")
                    break
        print("Total de vehículos encontrados: ",len(todas_urls))
 
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

        # Buscar la sección cuyo h2 termina con "resumen"
        section = None
        for sec in soup.find_all("section"):
            h2 = sec.find("h2")
            if h2 and h2.get_text(strip=True).lower().endswith("resumen"):
                section = sec
                break

        if not section:
            return data

        # Cada dato tiene:
        # <p class="text-muted...">Nombre</p>
        # <p class="font-medium...">Valor</p>

        for div in section.find_all("div"):
            ps = div.find_all("p", recursive=False)

            if len(ps) >= 2:
                nombre = ps[0].get_text(strip=True)
                valor = ps[1].get_text(strip=True)

                if nombre:
                    data[nombre] = valor

        return data

    @staticmethod
    def extraer_ficha_tecnica(soup: BeautifulSoup) -> Dict[str, Any]:
        data = {}

        # Buscar el h2 "Especificaciones"
        h2 = soup.find("h2", string=lambda s: s and s.strip() == "Especificaciones")

        if not h2:
            return data

        # El siguiente div contiene todas las tarjetas
        contenedor = h2.find_next("div")

        if not contenedor:
            return data

        for card in contenedor.find_all("div", class_=lambda c: c and "rounded-xl" in c):
            nombre = card.find("span")
            valor = card.find("p", class_=lambda c: c and "font-semibold" in c)

            if nombre and valor:
                data[
                    nombre.get_text(strip=True)
                ] = valor.get_text(strip=True)

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
                    "id_record": v.id,
                    "summary": v.summary,
                    "ficha_tecnica": v.ficha_tecnica,
                    "url":v.url
                })
        return all_entities
