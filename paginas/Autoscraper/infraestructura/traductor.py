# paginas/Autoscraper/infraestructura/traductor.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime
import re, json
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

    # eliminar todo lo que no sea número o separador
    s = re.sub(r"[^\d.,]", "", s)

    if s == "":
        return default

    # caso típico latino: 14.800 o 14,800
    if "." in s and "," not in s:
        s = s.replace(".", "")
    elif "," in s and "." not in s:
        s = s.replace(",", "")
    elif "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")

    try:
        return int(float(s))
    except:
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
        return float(s)
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

def _extract_cilindraje(version: str) -> Optional[str]:
        if not version:
            return None
        m = re.search(r'(\d{1,2}[\.,]\d)', version)
        if m:
            return m.group(1).replace(",", ".")
        m2 = re.search(r'\b(\d{1,2})\b(?=.*\s(L|litros|AC|TA|TM)\b|$)', version, flags=re.IGNORECASE)
        if m2:
            return m2.group(1)
        return None

def _infer_transmision(version: str, saving_plan_order: str) -> Optional[str]:
        if saving_plan_order:
            spo = saving_plan_order.strip().upper()
            if "AUTOM" in spo:
                return "Automática"
            if "MANU" in spo:
                return "Manual"
        v = (version or "").upper()
        if re.search(r'\bTA\b', v):
            return "Automática"
        if re.search(r'\bTM\b', v):
            return "Manual"
        return None


# =====================================================
# AUTOCOR
# =====================================================

class AutocorRecordTranslator:
    """
    Traduce la entidad cruda de Autocor a una fila normalizada.
    """
    def build_csv_row(self, e: Dict[str, Any]) -> Dict[str, Any]:
        id_record = _norm_str(_pick(e, "id_record", "id", "uuid", "vehicleId", "pilotId", default=""))
        placa = _norm_str(_pick(e, "placa", "plate", "license_plate", default=""))
        url = _norm_str(_pick(e, "media", "link", "href", "detailUrl","url", default=""))
        anio = _to_int(_pick(e, "anio", "year", "modelYear", default=0))

        if not id_record:
            id_record = f"AUTOCOR:{placa}:{anio}:{url}"

        row = {
            "id_record": id_record,
            "source": "autocor",
            "fecha_scrape": _now_iso(),

            "placa": placa,
            "anio": anio,
            "precio": _to_int(_pick(e, "precio", "prices", "amount", default=0)),
            "kilometraje": _to_int(_pick(e, "odometer", "kilometros", "km", "mileage", default=0)),
            "marca": _norm_str(_pick(e, "marca", "brand", "make", default="ND"), default="ND"),
            "modelo": _norm_str(_pick(e, "modelo", "model", default="ND"), default="ND"),
            "climateSystem":_norm_str(_pick(e, "climateSystem", default="ND"), default="ND"),
            "ciudad": _norm_str(_pick(e, "ciudad", "location", default="ND"), default="ND"),

            "color": _norm_str(_pick(e, "color", default="ND"), default="ND"),
            "motor": _norm_str(_extract_cilindraje(_pick(e, "version", default="ND")), default="ND"),
            "transmision": _norm_str(_infer_transmision(_pick(e, "version",  default=""),_pick(e, "saving_plan_order",  default="")), default="ND"),
            "traccion": _norm_str(_pick(e, "accesories","traccion", "drive", default="ND"), default="ND"),
            "interiorType": _norm_str(_pick(e, "interiorType", "tapizado", default="ND"), default="ND"),
            "fuelType": _norm_str(_pick(e, "fuel_name", "combustible", default="ND"), default="ND"),
            "motorType":_norm_str(_pick(e, "motorType", "engine_number", default="ND"), default="ND"),
            "typePago": _norm_str(_pick(e, "typePago", default="ND"), default="CONTADO"),
            "url": url,
            "productId": _norm_str(_pick(e, "id", "product_id", default="1"), default="1"),
            "json": json.dumps(e,ensure_ascii = False)       
        }

        # Defaults para columnas del modelo (si no vienen del portal)
        row.setdefault("fecha_ingreso", _now_iso())
        row.setdefault("direccion", None)
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
            "precio": _to_int(_pick(data, "Precio", "CashPrice", "Precio Contado", default=0)),
            "kilometraje": _to_int(_pick(data, "Recorrido", "Kilometraje", "km", "Mileage", default=0)),
            "marca": _norm_str(_pick(data, "Marca", "brand", "make", default="ND"), default="ND"),
            "modelo": _norm_str(_pick(data, "Modelo", "model", default="ND"), default="ND"),
            "climateSystem":_norm_str(_pick(e, "Sistema de climatización", default="ND"), default="ND"),
            "ciudad": _norm_str(_pick(data, "Ciudad", "city", default="ND"), default="ND"),

            "color": _norm_str(_pick(data, "Color", default="ND"), default="ND"),
            "motor": _norm_str(_pick(data, "Motor(cilindraje)", "engine", default="ND"), default="ND"),
            "transmision": _norm_str(_pick(data, "Transmisión", "transmission", default="ND"), default="ND"),
            "traccion": _norm_str(_pick(data, "Tracción", "drive", default="ND"), default="ND"),
            "direccion": _norm_str(_pick(data, "Dirección", default="ND"), default="ND"),
            "interiorType": _norm_str(_pick(data, "Tapizado", "InteriorType", default="ND"), default="ND"),
            "fuelType": _norm_str(_pick(data, "Combustible", "FuelType", default="ND"), default="ND"),
            "motorType": _norm_str(_pick(data, "Tipo de Motor", default="ND"), default="ND"),
            "typePago": _norm_str(_pick(data, "Tipo de pago", "PaymentType", default="ND"), default="ND"),
            "url": url,
            "productId": _norm_str(_pick(data, "id_record", "product_id","Product_id", default="1"), default="1"),
            "json": json.dumps(e,ensure_ascii = False)    
        }

        # Defaults para columnas del modelo (si no vienen del portal)
        row.setdefault("fecha_ingreso", _now_iso())

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
            "kilometraje": km,
            "precio": precio,
            "url": url,
            "productId": str(row.get("productId", "1")),

            "marca": row.get("marca", None),
            "modelo": row.get("modelo", None),
            "climateSystem": row.get("climateSystem", None),
            "traccion": row.get("traccion", None),
            "color": row.get("color", None),
            "motor":row.get("motor", None),
            "transmision": row.get("transmision", None),
            "direccion": row.get("direccion", None),
            "ciudad": row.get("ciudad", None),
            "interiorType": row.get("interiorType", None),
            "fuelType": row.get("fuelType", None),
            "motorType": row.get("motorType", None),
            "typePago": row.get("typePago", "CONTADO"),
            "json": str(row.get("json", "{}")),
            "DATA": None,
        }
