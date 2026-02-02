# autocor_solid/infra/translators.py
from __future__ import annotations
import re, json
from typing import Protocol, Dict, Any, Optional
import time

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

# Patio Tuerca ------------------------------

class PatioTuercaRecordTranslator:
    """Traduce los registros obtenidos del scraping de PatioTuerca a un formato estándar"""

    def translate(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte un registro crudo de PatioTuerca (que puede venir anidado) a un formato estándar."""

        # --- Desempaquetar niveles comunes ---
        ficha = rec.get("ficha_tecnica", {}) or rec.get("ficha", {})
        summary = rec.get("summary", {}) or rec.get("resumen", {})
        # --- Unificar todos los niveles posibles ---
        merged = {**rec, **summary, **ficha}
        # --- Mapeo estándar ---
        out = {
            "id_record": merged.get("id"),
            "marca": merged.get("Marca") or merged.get("Brand"),
            "modelo": merged.get("Modelo") or merged.get("Model"),
            "anio": merged.get("Año") or merged.get("Year"),
            "precio": merged.get("Precio") or merged.get("CashPrice") or merged.get("Precio Contado"),
            "kilometraje": merged.get("Recorrido") or merged.get("Kilometraje") or merged.get("Mileage"),
            "ciudad": merged.get("Ciudad") or merged.get("City"),
            "transmision": merged.get("Transmisión") or merged.get("Transmission"),
            "cilindraje": merged.get("Motor(cilindraje)") or merged.get("Engine"),
            "combustible": merged.get("Combustible") or merged.get("FuelType"),
            "traccion": merged.get("Tracción") or merged.get("Traction"),
            "direccion": merged.get("Dirección") or merged.get("Steering"),
            "tapizado": merged.get("Tapizado") or merged.get("InteriorType"),
            "tipo_pago": merged.get("Tipo de pago") or merged.get("PaymentType"),
            "descripcion": merged.get("Subtipo") or merged.get("Description"),
            "url": merged.get("url"),
            "fecha_ingreso": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        print("Esto es out: ",out)
        # --- Normalización de campos numéricos y texto ---
        # Año
        try:
            if out["anio"]:
                out["anio"] = int(str(out["anio"]).strip())
        except Exception:
            out["anio"] = None

        # Precio
        try:
            if out["precio"]:
                val = str(out["precio"]).replace("$", "").replace(".", "").replace(",", "").strip()
                out["precio"] = float(val)
        except Exception:
            out["precio"] = None

        # Kilometraje
        km_val = out.get("kilometraje")
        if km_val:
            try:
                km_clean = str(km_val).lower().replace("kms", "").replace("km", "").replace(".", "").replace(",", "").strip()
                out["kilometraje"] = int(km_clean)
            except Exception:
                out["kilometraje"] = None

        # Transmisión
        if "transmision" in out and out["transmision"]:
            val = str(out["transmision"]).lower()
            if "auto" in val:
                out["transmision"] = "Automática"
            elif "manu" in val:
                out["transmision"] = "Manual"
            else:
                out["transmision"] = None

        # Cilindraje
        if out.get("cilindraje"):
            val = str(out["cilindraje"]).strip()
            m = re.search(r"(\d{3,4})", val)
            if m:
                out["cilindraje"] = int(m.group(1))
            else:
                m2 = re.search(r"(\d{1,2}[\.,]\d)", val)
                if m2:
                    out["cilindraje"] = float(m2.group(1).replace(",", "."))
                else:
                    out["cilindraje"] = None

        # Limpiar strings vacíos
        for k, v in out.items():
            if isinstance(v, str) and not v.strip():
                out[k] = None

        # Guardar el JSON completo
        out["json"] = json.dumps(rec, ensure_ascii=False)
        print("Este es el out que sale: ",out)
        return out
    
    def build_csv_row(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        # aquí simplemente devuelves lo traducido
        return self.translate(rec)