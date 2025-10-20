# -*- coding: utf-8 -*-
"""
Autocor API → CSV con columnas:
id_record, maraca, model, transmision, cilindraje, kilometraje, fecha_ingreso, json

NUEVO:
- Merge con CSV existente validando vigencia por registro (default 1 día).
- Si el registro en CSV es "fresco" (< fresh_days), se conserva; si no, se actualiza.

Uso:
  python autocor_api_to_csv.py --out-csv datos/autocor_formato.csv --fresh-days 1
"""

import os, re, json, time, argparse, csv, datetime
from typing import Any, Dict, List, Optional
import requests

DEFAULT_BASE_URL = "https://www.autocor.com.ec/api/listPilot"

# ========= Utilidades de tiempo =========

def _parse_iso_dt(s: Optional[str]) -> Optional[datetime.datetime]:
    """
    Parsea ISO-8601 flexible: soporta 'Z' (UTC) o con offset.
    Devuelve datetime con tzinfo (si no hay, asume UTC).
    """
    if not s:
        return None
    try:
        # reemplaza Z por +00:00 para fromisoformat
        s2 = s.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            # asume UTC si no viene tz
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None

def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

def _is_fresh(dt: Optional[datetime.datetime], now: datetime.datetime, fresh_days: int) -> bool:
    if not dt:
        return False
    delta = now - dt
    return delta < datetime.timedelta(days=fresh_days)

# ========= Lógica de negocio existente =========

def extract_cilindraje(version: str) -> Optional[str]:
    if not version:
        return None
    m = re.search(r'(\d{1,2}[\.,]\d)', version)
    if m:
        return m.group(1).replace(",", ".")
    m2 = re.search(r'\b(\d{1,2})\b(?=.*\s(L|litros|AC|TA|TM)\b|$)', version, flags=re.IGNORECASE)
    if m2:
        return m2.group(1)
    return None

def infer_transmision(version: str, saving_plan_order: str) -> Optional[str]:
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

def translate_key(key: str) -> str:
    mapping = {
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
    return mapping.get(key, key)

def translate_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in rec.items():
        out[translate_key(k)] = v
    # derivados
    out["transmision"] = infer_transmision(rec.get("version", ""), rec.get("saving_plan_order", "") or "")
    cil = extract_cilindraje(rec.get("version", "")) or None
    if cil: out["cilindraje"] = cil
    # normaliza kilometraje si es posible
    if "kilometraje" in out:
        try: out["kilometraje"] = int(float(out["kilometraje"]))
        except Exception: pass
    return out

def fetch_page(session: requests.Session, base_url: str, page: int, method: str, timeout: int) -> Dict[str, Any]:
    params = {"page": page}
    if method == "GET":
        resp = session.get(base_url, params=params, timeout=timeout)
    else:
        url = f"{base_url}?page={page}"
        resp = session.post(url, data={}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

# ========= CSV helpers (merge por vigencia) =========

CSV_COLS = ["id_record", "maraca", "model", "transmision", "cilindraje", "kilometraje", "fecha_ingreso", "json"]

def _read_existing_csv(path: str) -> Dict[str, Dict[str, str]]:
    """
    Lee CSV existente y devuelve dict por id_record (como str) → fila (dict de columnas).
    Si el archivo no existe, devuelve {}.
    """
    if not os.path.exists(path):
        return {}
    rows: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if not row:
                continue
            key = str(row.get("id_record", "")).strip()
            if key:
                rows[key] = row
    return rows

def _build_new_row(rec: Dict[str, Any]) -> Dict[str, Any]:
    transmision = infer_transmision(rec.get("version", ""), rec.get("saving_plan_order", "") or "")
    cil = extract_cilindraje(rec.get("version", ""))
    rec_es = translate_record(rec)  # para la columna json

    return {
        "id_record": rec.get("id_record"),
        "maraca": rec.get("brand"),                  # (con 'maraca' tal como lo pediste)
        "model": rec.get("model"),
        "transmision": transmision or "",
        "cilindraje": cil or "",
        "kilometraje": rec.get("odometer"),
        "fecha_ingreso": rec.get("created_dt"),
        "json": json.dumps(rec_es, ensure_ascii=False),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--out-csv", default="datos/autocor_formato.csv")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--fresh-days", type=int, default=1, help="Vigencia en días para conservar registros del CSV")
    ap.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutocorScraper/1.0")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent, "Accept": "application/json"})

    # 1) Descubrir cantidad de páginas (GET primero, luego POST)
    first_ok, first_data, last_err = None, None, None
    for m in ("GET", "POST"):
        try:
            first_data = fetch_page(session, args.base_url, 1, m, args.timeout)
            first_ok = m
            break
        except Exception as e:
            last_err = e
    if first_ok is None:
        raise RuntimeError(f"No se pudo leer la página 1: {last_err}")

    page_count = int(first_data.get("aditional_data", {}).get("page_count", 1))
    entities = list(first_data.get("entitydata", []) or [])

    # 2) Resto de páginas
    for page in range(2, page_count + 1):
        for attempt in range(1, args.retries + 1):
            try:
                data = fetch_page(session, args.base_url, page, first_ok, args.timeout)
                entities.extend(data.get("entitydata", []) or [])
                break
            except Exception as e:
                if attempt >= args.retries:
                    print(f"[WARN] Página {page} falló: {e}")
                else:
                    time.sleep(1.2 * attempt)

    # 3) Cargar CSV existente y fusionar por vigencia
    existing = _read_existing_csv(args.out_csv)
    now = _now_utc()
    fresh_days = max(0, int(args.fresh_days))

    kept, updated, added = 0, 0, 0
    merged: Dict[str, Dict[str, Any]] = dict(existing)  # empieza con lo existente

    for rec in entities:
        new_row = _build_new_row(rec)
        key = str(new_row["id_record"])
        if not key:
            # sin id_record no podemos aplicar merge; agrega igual
            merged[key] = new_row
            added += 1
            continue

        if key in existing:
            # Hay versión en CSV: decidir por vigencia
            old_row = existing[key]
            old_dt = _parse_iso_dt(old_row.get("fecha_ingreso"))
            if _is_fresh(old_dt, now, fresh_days):
                # Mantener la fila del CSV (vigente)
                kept += 1
            else:
                # Reemplazar por nueva (vencida)
                merged[key] = new_row
                updated += 1
        else:
            # No existe en CSV → agregar
            merged[key] = new_row
            added += 1

    # 4) Escribir CSV final (orden estable por id_record)
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        for _, row in sorted(merged.items(), key=lambda kv: (str(kv[0]))):
            # Asegura que estén todas las columnas (si faltó 'json' en existente viejo, por ejemplo)
            out_row = {c: row.get(c, "") for c in CSV_COLS}
            w.writerow(out_row)

    total = len(merged)
    print(f"✓ Merge completado → Total filas: {total} | Conservadas vigentes: {kept} | Actualizadas: {updated} | Nuevas: {added}")
    print(f"✓ CSV: {args.out_csv}")

if __name__ == "__main__":
    main()

