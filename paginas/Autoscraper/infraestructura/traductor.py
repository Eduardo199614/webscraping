# autocor_solid/infra/translators.py
from __future__ import annotations
import re, json
from typing import Protocol, Dict, Any, Optional

class RecordTranslator(Protocol):
    def translate(self, rec: Dict[str, Any]) -> Dict[str, Any]: ...
    def build_csv_row(self, rec: Dict[str, Any]) -> Dict[str, Any]: ...

class AutocorRecordTranslator(RecordTranslator):
    _mapping = {
        "id_record": "id_registro",
        "id": "id",
        "media": "media",
        "brand": "marca",
        "model": "modelo",
        "prices": "precio",
        "year": "anio",
        "owner": "duenio",
        "home": "domicilio",
        "odometer": "kilometraje",
        "type": "tipo",
        "location": "ubicacion",
        "business_channel": "canal_negocio",
        "processedAt": "procesado_el",
        "color": "color",
        "accesories": "accesorios",
        "license_plate": "placa",
        "received_flag": "bandera_recibido",
        "days_in_stock": "dias_en_stock",
        "published_in_web": "publicado_en_web",
        "engine_number": "numero_motor",
        "reserved_by_user_email": "reservado_por_email",
        "reserved_by_user_name": "reservado_por_nombre",
        "reserved_dt": "reservado_el",
        "expiration_dt": "expira_el",
        "opportunity_sale_id": "id_oportunidad_venta",
        "factory_invoicing_dt": "facturado_fabrica_el",
        "factory_status": "estado_fabrica",
        "status_name": "estado",
        "fuel_name": "combustible",
        "availability_status_name": "disponibilidad",
        "availability_status_code": "codigo_disponibilidad",
        "created_fullname": "creado_por",
        "created_dt": "fecha_ingreso",
        "deleted_flag": "bandera_eliminado",
        "owner_branch_code": "sucursal_duenio",
        "saving_plan_group": "grupo",
        "saving_plan_order": "transmision_bruta",
        "integration_reference_code": "codigo_referencia_integracion",
        "version": "version",
        "purchase_price": "precio_compra",
    }

    def translate(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        out = { self._mapping.get(k, k): v for k, v in rec.items() }

        # Derivados
        out["transmision"] = self._infer_transmision(rec.get("version", ""), rec.get("saving_plan_order", "") or "")
        cil = self._extract_cilindraje(rec.get("version", ""))
        if cil:
            out["cilindraje"] = cil

        # Normalización
        if "kilometraje" in out:
            try:
                out["kilometraje"] = int(float(out["kilometraje"]))
            except Exception:
                pass

        return out

    def build_csv_row(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        rec_es = self.translate(rec)
        return {
            "id_record": rec.get("id_record"),
            "maraca": rec.get("brand"),              # (intencional: "maraca" tal como lo pediste)
            "model": rec.get("model"),
            "transmision": rec_es.get("transmision", ""),
            "cilindraje": rec_es.get("cilindraje", ""),
            "kilometraje": rec.get("odometer"),
            "fecha_ingreso": rec.get("created_dt"),
            "json": json.dumps(rec_es, ensure_ascii=False),
        }

    @staticmethod
    def _extract_cilindraje(version: str) -> Optional[str]:
        if not version:
            return None
        m = re.search(r'(\d{1,2}[\.,]\d)', version)
        if m:
            return m.group(1).replace(",", ".")
        m2 = re.search(r'\b(\d{1,2})\b(?=.*\s(L|litros|AC|TA|TM)\b|$)', version, flags=re.IGNORECASE)
        if m2:
            return m2.group(1)
        return None

    @staticmethod
    def _infer_transmision(version: str, saving_plan_order: str) -> Optional[str]:
        if saving_plan_order:
            spo = saving_plan_order.strip().upper()
            if "AUTOM" in spo:
                return "Automática"
            if "MANU" in spo:
                return "Manual"
        v = (version or "").upper()
        if re.search(r'\bTA\b', v):
            return "Automática"
        if re.search(r'\bTM\b', v):
            return "Manual"
        return None
