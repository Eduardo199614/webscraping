# autocor_solid/domain/models.py
from __future__ import annotations
import datetime
from typing import Optional
#-Patiotuerca
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

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

def now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

CSV_COLS = ["id_record", "marca", "model", "transmision", "cilindraje", "kilometraje", "fecha_ingreso", "json"]


#--------------- PatioTuerca

@dataclass
class FichaAuto:
    id_auto: str | None
    fecha_ingreso: datetime
    estado: str
    datos: Dict[str, Any]    # ← contiene TODO: summary + ficha técnica
    mensaje: str
    tiempo: float
    ejecucion_exitosa: bool