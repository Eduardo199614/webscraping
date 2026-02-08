# infraestructura/AutosBDD/Api_Condelpi.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, time
import requests
from dataclasses import dataclass
from typing import Any, Dict, Optional


class CondelpiError(Exception):
    pass


@dataclass(frozen=True)
class CondelpiConfig:
    base_url: str
    usuario: str
    password: str
    api_key: str
    timeout: int = 20
    retries: int = 3

    @staticmethod
    def from_env(timeout: Optional[int] = None, retries: Optional[int] = None) -> "CondelpiConfig":
        base_url = os.getenv("CONDELPI_BASE_URL", "https://apc.condelpi.com").rstrip("/")
        usuario = os.getenv("CONDELPI_USUARIO", "").strip()
        password = os.getenv("CONDELPI_PASSWORD", "").strip()
        api_key = os.getenv("CONDELPI_KEY", "").strip()

        if not usuario or not password or not api_key:
            raise CondelpiError("Faltan env vars: CONDELPI_USUARIO / CONDELPI_PASSWORD / CONDELPI_KEY")

        if timeout is None:
            timeout = int(os.getenv("HTTP_TIMEOUT", "20"))
        if retries is None:
            retries = int(os.getenv("CONDELPI_RETRIES", "3"))

        return CondelpiConfig(
            base_url=base_url,
            usuario=usuario,
            password=password,
            api_key=api_key,
            timeout=int(timeout),
            retries=int(retries),
        )


class CondelpiClient:
    def __init__(self, cfg: CondelpiConfig, session: Optional[requests.Session] = None):
        self.cfg = cfg
        self.s = session or requests.Session()
        self._token: Optional[str] = None
        self._token_exp: Optional[float] = None

    def _url(self, path: str) -> str:
        return f"{self.cfg.base_url}/{path.lstrip('/')}"

    def _sleep_backoff(self, attempt: int) -> None:
        time.sleep(0.7 * (attempt + 1))

    def _request(self, method: str, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        last_exc: Optional[Exception] = None

        for attempt in range(self.cfg.retries + 1):
            try:
                r = self.s.request(method, url, headers=headers, json=payload, timeout=self.cfg.timeout)
                try:
                    data = r.json()
                except Exception:
                    data = {"raw": r.text}

                if r.status_code >= 400:
                    raise CondelpiError(f"HTTP {r.status_code}: {data}")

                return data

            except (requests.Timeout, requests.ConnectionError, CondelpiError) as e:
                last_exc = e
                if attempt < self.cfg.retries:
                    self._sleep_backoff(attempt)
                    continue
                raise CondelpiError(f"Error Condelpi (final): {e}") from e

        raise CondelpiError(f"Error Condelpi desconocido: {last_exc}")

    def _token_is_valid(self) -> bool:
        if not self._token:
            return False
        if self._token_exp and time.time() >= self._token_exp:
            return False
        return True

    def login(self) -> str:
        url = self._url("/apc_api/api/Login")
        payload = {"Usuario": self.cfg.usuario, "Password": self.cfg.password}
        headers = {"Content-Type": "application/json"}

        data = self._request("POST", url, headers, payload)

        token = (
            data.get("token")
            or data.get("access_token")
            or data.get("Token")
            or data.get("data", {}).get("token")
        )
        if not token:
            raise CondelpiError(f"Login OK pero no vino token: {data}")

        expires_in = data.get("expires_in") or data.get("ExpiresIn")
        if isinstance(expires_in, (int, float)) and expires_in > 0:
            self._token_exp = time.time() + float(expires_in) - 30
        else:
            self._token_exp = time.time() + 50 * 60  # 50 min

        self._token = token
        return token

    def get_token(self) -> str:
        if self._token_is_valid():
            return self._token  # type: ignore
        return self.login()

    def enviar_reventa(self, payload_reventa: Dict[str, Any]) -> Dict[str, Any]:
        url = self._url("/APC_API/api/REVENTAS9")

        payload_reventa.setdefault("key", self.cfg.api_key)

        token = self.get_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        try:
            return self._request("POST", url, headers, payload_reventa)
        except CondelpiError:
            # relogueo 1 vez
            self._token = None
            self._token_exp = None
            token = self.get_token()
            headers["Authorization"] = f"Bearer {token}"
            return self._request("POST", url, headers, payload_reventa)
