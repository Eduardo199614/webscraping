from __future__ import annotations
from typing import Protocol, Dict, Any
from bs4 import BeautifulSoup
import requests
import re
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
            "ficha_tecnica": FichaExtractor.extraer_ficha_tecnica(soup)
        }
