# autocor_solid/domain/services.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Tuple
from .politicas import FreshnessPolicy
from .modelo import now_utc

@dataclass
class MergeService:
    freshness: FreshnessPolicy

    def merge(
        self,
        existing: Dict[str, Dict[str, str]],
        incoming_rows: Iterable[Dict[str, Any]],
        id_field: str = "id_record"
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
        """Funde datasets aplicando FreshnessPolicy; devuelve (merged, métricas)."""
        ref = now_utc()
        merged = dict(existing)
        kept = updated = added = 0

        for row in incoming_rows:
            key = str(row.get(id_field, "")).strip()
            if not key:
                # Sin id: no aplica policy; igual se incorpora
                phantom_key = f"__NOID__{id(row)}"
                merged[phantom_key] = row
                added += 1
                continue

            if key in existing:
                if self.freshness.is_fresh(existing[key], ref):
                    kept += 1
                else:
                    merged[key] = row
                    updated += 1
            else:
                merged[key] = row
                added += 1

        metrics = {"kept": kept, "updated": updated, "added": added, "total": len(merged)}
        return merged, metrics
