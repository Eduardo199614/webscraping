# paginas/Autoscraper/dominio/servicios.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

class MergeService:
    def __init__(self, freshness_policy):
        self.freshness_policy = freshness_policy

    def merge(
        self,
        existing_rows: List[Dict[str, Any]],
        incoming_rows: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[Dict[str, Any]]]:
        """
        existing_rows: estado actual (lista de filas, tal cual vienen del CSV)
        incoming_rows: filas nuevas a comparar

        La URL es la clave de identidad real (id_record no es único).
        Filas sin URL se agregan siempre, sin poder verificar duplicado.

        Retorna:
        - merged_rows (estado final, lista completa)
        - metrics
        - delta_rows (solo las filas added/updated)
        """
        # Índice interno por URL normalizada, solo para esta operación
        by_url: Dict[str, Dict[str, Any]] = {}
        no_url_rows: List[Dict[str, Any]] = []

        for row in existing_rows:
            url = self._norm_url(row.get("url", ""))
            if url:
                by_url[url] = row
            else:
                no_url_rows.append(row)

        delta: List[Dict[str, Any]] = []
        kept = 0
        updated = 0
        added = 0

        for row in incoming_rows:
            url = self._norm_url(row.get("url", ""))

            if not url:
                # sin URL no podemos verificar duplicado, se agrega igual
                no_url_rows.append(row)
                delta.append(row)
                added += 1
                continue

            prev = by_url.get(url)

            if prev is None:
                by_url[url] = row
                delta.append(row)
                added += 1
                continue

            # si el previo está "fresco", lo conservamos tal cual
            if self.freshness_policy.is_fresh(prev, row):
                kept += 1
                continue

            # si no está fresco, actualizamos
            by_url[url] = row
            delta.append(row)
            updated += 1

        merged = list(by_url.values()) + no_url_rows

        metrics = {
            "total": len(merged),
            "kept": kept,
            "updated": updated,
            "added": added,
        }
        return merged, metrics, delta

    @staticmethod
    def _norm_url(url: str) -> str:
        return str(url).strip().rstrip("/")
