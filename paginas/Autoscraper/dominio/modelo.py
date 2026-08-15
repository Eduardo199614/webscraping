# paginas/Autoscraper/dominio/modelo.py
from __future__ import annotations
import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ---------------- Autocor helpers (si los usas en otros lados)
def parse_iso_dt(s: Optional[str]) -> Optional[datetime.datetime]:
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)

# ---------------- PatioTuerca model (si lo usas)
@dataclass
class Vehiculo:
    id: str
    summary: Dict[str, Any]
    ficha_tecnica: Dict[str, Any]
    url: str

# Años objetivo
ANIOS_OBJETIVO = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

# ✅ CSV_COLS debe incluir TODO lo que producen tus translators + lo que Condelpi necesita
CSV_COLS = [
    "id_record",
    "source",
    "fecha_scrape",

    "placa",
    "marca",
    "modelo",
    "anio",
    "precio",
    "kilometraje",
    "climateSystem",
    "ciudad",

    "transmision",
    "motor",
    "fuelType",
    "traccion",
    "direccion",
    "interiorType",
    "typePago",
    "descripcion",
    "fecha_ingreso",

    "color",
    "motorType",
    "productId",

    "url",
    "json",
]
