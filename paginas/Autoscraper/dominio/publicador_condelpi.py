# dominio/publicador_condelpi.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

@dataclass
class PublicadorCondelpi:
    client: Any  # CondelpiClient

    def map_auto_a_reventa(self, auto: Dict) -> Dict:
        """
        auto: registro obtenido del web scraping (PatioTuerca / AutoCor / merge).
        Ajusta las llaves de abajo a tu estructura real.
        """
        return {
            # key se setea dentro de enviar_reventa()
            "placa": auto.get("placa") or auto.get("plate"),
            "vin": auto.get("vin") or auto.get("chasis"),
            "marca": auto.get("marca") or auto.get("brand"),
            "modelo": auto.get("modelo") or auto.get("model"),
            "anio": auto.get("anio") or auto.get("year"),
            "precio": auto.get("precio") or auto.get("price"),
            "kilometraje": auto.get("kilometraje") or auto.get("km"),
            "color": auto.get("color"),
            "ciudad": auto.get("ciudad") or auto.get("location"),
            "fuente": auto.get("fuente") or auto.get("source"),   # "Patiotuerca" / "Autocor"
            "url": auto.get("url") or auto.get("link"),
            # agrega aquí campos extra que pida REVENTAS9
        }

    def enviar_autos(self, autos: List[Dict]) -> Dict:
        """
        Envía uno por uno (más seguro, y te deja ver cuál falla).
        """
        enviados: List[Dict] = []
        fallidos: List[Dict] = []

        for idx, auto in enumerate(autos, start=1):
            payload = self.map_auto_a_reventa(auto)

            try:
                resp = self.client.enviar_reventa(payload)
                enviados.append({"i": idx, "payload": payload, "resp": resp})
            except Exception as e:
                fallidos.append({"i": idx, "payload": payload, "error": str(e)})

        return {
            "total": len(autos),
            "ok": len(fallidos) == 0,
            "enviados": len(enviados),
            "fallidos": len(fallidos),
            "detalle_fallidos": fallidos[:10],  # no explotar consola
        }
