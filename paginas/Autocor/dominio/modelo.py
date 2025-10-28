# autocor_solid/domain/models.py
from __future__ import annotations
import datetime
from typing import Optional

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
