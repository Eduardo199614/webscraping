# paginas/Autoscraper/dominio/politicas.py
from __future__ import annotations
import datetime
from typing import Dict, Any, Optional

def _parse_iso(s: str) -> Optional[datetime.datetime]:
    try:
        # soporta "Z"
        s = s.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None

class ByDaysFreshnessPolicy:
    def __init__(self, fresh_days: int):
        self.fresh_days = int(fresh_days)

    def is_fresh(self, prev_row: Dict[str, Any], new_row: Dict[str, Any]) -> bool:
        """
        Retorna True si prev_row todavía se considera vigente y NO debería ser reemplazado.
        Usa fecha_scrape de prev_row.
        """
        if self.fresh_days <= 0:
            return False  # si no hay vigencia, siempre deja actualizar

        reference = datetime.datetime.now(datetime.timezone.utc)

        prev_dt = None
        fs = prev_row.get("fecha_scrape")
        if isinstance(fs, datetime.datetime):
            prev_dt = fs
            if prev_dt.tzinfo is None:
                prev_dt = prev_dt.replace(tzinfo=datetime.timezone.utc)
        elif isinstance(fs, str) and fs.strip():
            prev_dt = _parse_iso(fs.strip())

        if not prev_dt:
            # si no hay fecha, no podemos considerarlo fresco
            return False

        return (reference - prev_dt) < datetime.timedelta(days=self.fresh_days)
