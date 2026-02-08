# paginas/Autoscraper/dominio/servicios.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

class MergeService:
    def __init__(self, freshness_policy):
        self.freshness_policy = freshness_policy

    def merge(
        self,
        existing_by_id: Dict[str, Dict[str, Any]],
        incoming_rows: List[Dict[str, Any]],
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int], Dict[str, Dict[str, Any]]]:
        """
        existing_by_id: estado actual (id_record -> row)
        incoming_rows: filas nuevas a comparar

        Retorna:
        - merged_by_id (estado final)
        - metrics
        - delta_by_id (solo added/updated)
        """
        merged = dict(existing_by_id)  # copia
        delta: Dict[str, Dict[str, Any]] = {}

        kept = 0
        updated = 0
        added = 0

        for row in incoming_rows:
            rid = str(row.get("id_record", "")).strip()
            if not rid:
                # si falta id_record, lo ignoramos (o podrías generarlo aquí)
                continue

            prev = merged.get(rid)

            if prev is None:
                merged[rid] = row
                delta[rid] = row
                added += 1
                continue

            # si el previo está "fresco", lo conservamos
            if self.freshness_policy.is_fresh(prev, row):
                kept += 1
                continue

            # si no está fresco, actualizamos
            merged[rid] = row
            delta[rid] = row
            updated += 1

        metrics = {
            "total": len(merged),
            "kept": kept,
            "updated": updated,
            "added": added,
        }
        return merged, metrics, delta
