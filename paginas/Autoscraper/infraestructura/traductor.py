# paginas/Autoscraper/infraestructura/traductor.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from datetime import datetime
import re
def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _pick(d: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    for k in keys:
        if k in d and d.get(k) not in (None, "", [], {}):
            return d.get(k)
    return default

def _to_int(x: Any, default: int = 0) -> int:
    if x is None:
        return default

    s = str(x).lower().strip()

    if s == "":
        return default

    # eliminar símbolos comunes
    s = re.sub(r"[^\d.,]", "", s)

    if s == "":
        return default

    # normalizar separadores
    if s.count(",") > s.count("."):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        return int(float(s))
    except Exception:
        return default

def _to_float(x: Any, default: float = 0.0) -> float:
    if x is None:
        return default

    s = str(x).lower().strip()
    if s == "":
        return default

    # eliminar texto y símbolos (excepto números, punto y coma)
    s = re.sub(r"[^\d.,]", "", s)
    if s == "":
        return default

    # normalizar separadores
    if s.count(",") > s.count("."):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        return float(s) * 1000 #en miles
    except Exception:
        return default

def _norm_str(x: Any, default: str = "") -> str:
    if x is None:
        return default
    s = str(x).strip()
    return s if s else default

def _merge_levels(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    merged = {}
    for d in dicts:
        if isinstance(d, dict):
            merged.update(d)
    return merged


# =====================================================
# AUTOCOR
# =====================================================

class AutocorRecordTranslator:
    """
    Traduce la entidad cruda de Autocor a una fila normalizada.
    """
    def build_csv_row(self, e: Dict[str, Any]) -> Dict[str, Any]:
        id_record = _norm_str(_pick(e, "id_record", "id", "uuid", "vehicleId", "pilotId", default=""))
        placa = _norm_str(_pick(e, "placa", "plate", "licensePlate", default=""))
        url = _norm_str(_pick(e, "url", "link", "href", "detailUrl", default=""))
        anio = _to_int(_pick(e, "anio", "year", "modelYear", default=0))

        if not id_record:
            id_record = f"AUTOCOR:{placa}:{anio}:{url}"

        row = {
            "id_record": id_record,
            "source": "autocor",
            "fecha_scrape": _now_iso(),

            "placa": placa,
            "anio": anio,
            "precio": _to_float(_pick(e, "precio", "price", "amount", default=0)),
            "kilometraje": _to_int(_pick(e, "kilometraje", "kilometros", "km", "mileage", default=0)),
            "marca": _norm_str(_pick(e, "marca", "brand", "make", default="ND"), default="ND"),
            "modelo": _norm_str(_pick(e, "modelo", "model", default="ND"), default="ND"),
            "ciudad": _norm_str(_pick(e, "ciudad", "city", default="ND"), default="ND"),

            "color": _norm_str(_pick(e, "color", default="ND"), default="ND"),
            "motor": _norm_str(_pick(e, "motor", "engine", default="ND"), default="ND"),
            "transmision": _norm_str(_pick(e, "transmision", "transmission", default="ND"), default="ND"),
            "traccion": _norm_str(_pick(e, "traccion", "drive", default="ND"), default="ND"),
            "direccion": _norm_str(_pick(e, "direccion", default="ND"), default="ND"),

            "url": url,
            "productId": _norm_str(_pick(e, "productId", "product_id", default="1"), default="1"),
        }

        # Defaults para columnas del modelo (si no vienen del portal)
        row.setdefault("cilindraje", "ND")
        row.setdefault("combustible", "ND")
        row.setdefault("tapizado", "ND")
        row.setdefault("tipo_pago", "CONTADO")
        row.setdefault("descripcion", "ND")
        row.setdefault("fecha_ingreso", _now_iso())
        row.setdefault("json", "{}")

        return row


# =====================================================
# PATIOTUERCA
# =====================================================

class PatioTuercaRecordTranslator:
    """
    Traduce la entidad cruda de PatioTuerca a una fila normalizada.
    """
    def build_csv_row(self, e: Dict[str, Any]) -> Dict[str, Any]:
        id_record = _norm_str(_pick(e, "id_record", "id", "uuid", "publicationId", "adId", default=""))
        summary = e.get("summary", {})
        ficha = e.get("ficha_tecnica", {})
        data = _merge_levels(e, summary, ficha)
        

        placa = _norm_str(_pick(data, "Placa", "plate", "licensePlate", default=""))
        url = _norm_str(_pick(data, "url", "link", "href", "detailUrl", default=""))
        anio = _to_int(_pick(data, "Año", "year", "modelYear", default=0))

        if not id_record:
            id_record = f"PATIOTUERCA:{placa}:{anio}:{url}"

        row = {
            "id_record": id_record,
            "source": "patiotuerca",
            "fecha_scrape": _now_iso(),

            "placa": placa,
            "anio": anio,
            "precio": _to_float(_pick(data, "Precio", "CashPrice", "Precio Contado", default=0)),
            "kilometraje": _to_int(_pick(data, "Recorrido", "Kilometraje", "km", "Mileage", default=0)),
            "marca": _norm_str(_pick(data, "Marca", "brand", "make", default="ND"), default="ND"),
            "modelo": _norm_str(_pick(data, "Modelo", "model", default="ND"), default="ND"),
            "ciudad": _norm_str(_pick(data, "Ciudad", "city", default="ND"), default="ND"),

            "color": _norm_str(_pick(data, "Color", default="ND"), default="ND"),
            "motor": _norm_str(_pick(data, "Motor(cilindraje)", "engine", default="ND"), default="ND"),
            "transmision": _norm_str(_pick(data, "Transmisión", "transmission", default="ND"), default="ND"),
            "traccion": _norm_str(_pick(data, "Tracción", "drive", default="ND"), default="ND"),
            "direccion": _norm_str(_pick(data, "Dirección", default="ND"), default="ND"),

            "url": url,
            "productId": _norm_str(_pick(data, "ProductID", "product_id","Product_id", default="1"), default="1"),
        }

        # Defaults para columnas del modelo (si no vienen del portal)
        row.setdefault("cilindraje", "ND")
        row.setdefault("combustible", "ND")
        row.setdefault("tapizado", "ND")
        row.setdefault("tipo_pago", "CONTADO")
        row.setdefault("descripcion", "ND")
        row.setdefault("fecha_ingreso", _now_iso())
        row.setdefault("json", "{}")

        return row


# =====================================================
# CONDELPI
# =====================================================

class CondelpiPayloadTranslator:
    """
    Convierte una row normalizada (salida de Autocor/PatioTuerca translators)
    al payload requerido por Condelpi REVENTAS9.
    """
    def build_payload(self, row: Dict[str, Any]) -> Dict[str, Any]:
        placa = str(row.get("placa", "")).strip()
        anio = int(row.get("anio", 0) or 0)
        km = int(row.get("kilometraje", row.get("kilometros", 0)) or 0)
        precio = float(row.get("precio", 0) or 0)
        url = str(row.get("url", row.get("link", ""))).strip()

        # ✅ payload base (puedes ajustar si Condelpi exige campos específicos)
        return {
            "placa": placa,
            "anio": anio,
            "kilometros": km,
            "precio": precio,
            "url": url,
            "productId": str(row.get("productId", "1")),

            "marca": str(row.get("marca", "ND")),
            "modelo": str(row.get("modelo", "ND")),
            "traccion": str(row.get("traccion", "ND")),
            "color": str(row.get("color", "ND")),
            "motor": str(row.get("motor", "ND")),
            "transmision": str(row.get("transmision", "ND")),
            "direccion": str(row.get("direccion", "ND")),
            "ciudad": str(row.get("ciudad", "ND")),

            "json": str(row.get("json", "{}")),
            "DATA": None,
        }
