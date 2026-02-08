# infraestructura/publisher_condelpi.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CondelpiPublisher:
    client: Any  # CondelpiClient

    def map_row_to_reventa(self, row: Dict, fuente: str) -> Dict:
        """
        ✅ AQUÍ ajustas el mapping según cómo viene tu `delta`
        (las llaves que produce translator/merger).
        """
        return {
            "fuente": fuente,

            # ===== EJEMPLO (AJUSTA) =====
            "placa": row.get("placa") or row.get("PLACA") or row.get("plate"),
            "vin": row.get("vin") or row.get("VIN") or row.get("chasis"),
            "marca": row.get("marca") or row.get("MARCA") or row.get("brand"),
            "modelo": row.get("modelo") or row.get("MODELO") or row.get("model"),
            "anio": row.get("anio") or row.get("ANIO") or row.get("year"),
            "precio": row.get("precio") or row.get("PRECIO") or row.get("price"),
            "kilometraje": row.get("kilometraje") or row.get("KM") or row.get("km"),
            "url": row.get("url") or row.get("URL") or row.get("link"),
        }

    def publish(self, delta_rows: List[Dict], fuente: str) -> Dict:
        enviados = 0
        fallidos: List[Dict] = []

        for i, row in enumerate(delta_rows, start=1):
            payload = self.map_row_to_reventa(row, fuente=fuente)
            try:
                self.client.enviar_reventa(payload)
                enviados += 1
            except Exception as e:
                fallidos.append({"i": i, "error": str(e), "payload": payload})

        return {
            "enviados": enviados,
            "fallidos": len(fallidos),
            "detalle_fallidos": fallidos[:10],
        }
