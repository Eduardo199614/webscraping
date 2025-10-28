# autocor_solid/domain/policies.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict
import datetime
from .modelo import parse_iso_dt

class FreshnessPolicy(Protocol):
    def is_fresh(self, old_row: Dict[str, str], reference: datetime.datetime) -> bool:
        """Retorna True si la fila existente está vigente."""
        ...

@dataclass(frozen=True)
class ByDaysFreshnessPolicy(FreshnessPolicy):
    fresh_days: int
    date_field: str = "fecha_ingreso"

    def is_fresh(self, old_row: Dict[str, str], reference: datetime.datetime) -> bool:
        if self.fresh_days <= 0:
            return False
        dt = parse_iso_dt(old_row.get(self.date_field))
        if not dt:
            return False
        return (reference - dt) < datetime.timedelta(days=self.fresh_days)

# (Ejemplo alternativo, si un día lo quieres)
@dataclass(frozen=True)
class ByHoursFreshnessPolicy(FreshnessPolicy):
    hours: int
    date_field: str = "fecha_ingreso"

    def is_fresh(self, old_row: Dict[str, str], reference: datetime.datetime) -> bool:
        if self.hours <= 0:
            return False
        dt = parse_iso_dt(old_row.get(self.date_field))
        if not dt:
            return False
        return (reference - dt) < datetime.timedelta(hours=self.hours)
