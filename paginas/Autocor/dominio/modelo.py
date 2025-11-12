# autocor_solid/domain/models.py
from __future__ import annotations
from typing import Optional
import datetime
#-Patiotuerca
from dataclasses import dataclass
from typing import Dict, Any


#--------------Autocor
def parse_iso_dt(s: Optional[str]) -> Optional[datetime.datetime]:
    """ISO flexible: soporta 'Z' → UTC y offsets. Devuelve tz-aware."""
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




#--------------- PatioTuerca
@dataclass
class Vehiculo: #formato de como parsear_html de la clase en api_cliente_PatioTuerca devuelve la informacion (usado posterior a la llamada de parsear_html)
    id: str
    summary: Dict[str, Any]
    ficha_tecnica: Dict[str, Any]
    url: str
# Años que vas a procesar en lotes
ANIOS_OBJETIVO =   [2015] # ejemplo: 2015–2025 list(range(2015, 2026))
#el [2015] para pruebas
CSV_COLS = [ #Modificado al formato de datos completo pedido por el cliente (Como tenían en la base de PatioTuerca de ellos)
    "id_record",
    "marca",
    "modelo",
    "anio",
    "precio",
    "kilometraje",
    "ciudad",
    "transmision",
    "cilindraje",
    "combustible",
    "traccion",
    "direccion",
    "tapizado",
    "tipo_pago",
    "descripcion",
    "fecha_ingreso",
    "url",
    "json"
]
