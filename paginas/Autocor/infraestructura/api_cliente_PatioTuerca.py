# autocor_solid/infra/api_client.py
from __future__ import annotations
from typing import Protocol, Tuple, List, Dict, Any, Optional
import time, requests

DEFAULT_BASE_URL = "https://www.autocor.com.ec/api/listPilot"

class ApiClient(Protocol):
    def discover_first_page(self) -> Tuple[int, List[Dict[str, Any]]]: ...
    def fetch_page(self, page: int) -> List[Dict[str, Any]]: ...

class RequestsApiClientPT(ApiClient):
    def __init__(self, base_url: str, user_agent: str, timeout: int = 20, retries: int = 3):
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})
        self._method: Optional[str] = None  # "GET" o "POST"

    def _fetch_page(self, page: int, method: str) -> Dict[str, Any]:
        params = {"page": page}
        if method == "GET":
            resp = self.session.get(self.base_url, params=params, timeout=self.timeout)
        else:
            url = f"{self.base_url}?page={page}"
            resp = self.session.post(url, data={}, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def discover_first_page(self) -> Tuple[int, List[Dict[str, Any]]]:
        last_err = None
        for m in ("GET", "POST"):
            try:
                data = self._fetch_page(1, m)
                self._method = m
                page_count = int(data.get("aditional_data", {}).get("page_count", 1))
                entities = list(data.get("entitydata", []) or [])
                return page_count, entities
            except Exception as e:
                last_err = e
        raise RuntimeError(f"No se pudo leer la página 1: {last_err}")

    def fetch_page(self, page: int) -> List[Dict[str, Any]]:
        if not self._method:
            self.discover_first_page()
        assert self._method is not None
        for attempt in range(1, self.retries + 1):
            try:
                data = self._fetch_page(page, self._method)
                return list(data.get("entitydata", []) or [])
            except Exception:
                if attempt >= self.retries:
                    raise
                time.sleep(1.2 * attempt)