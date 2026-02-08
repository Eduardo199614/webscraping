# paginas/Autoscraper/infraestructura/repositorio.py
from __future__ import annotations
import os, csv, json
from typing import Protocol, Dict, Any

from paginas.Autoscraper.dominio.modelo import CSV_COLS
from paginas.Autoscraper.infraestructura.AutosBDD.Api_Condelpi import CondelpiClient
from paginas.Autoscraper.infraestructura.traductor import CondelpiPayloadTranslator


# =====================================================
# CONTRATO DE REPOSITORIO
# =====================================================

class Repository(Protocol):
    def load(self) -> Dict[str, Dict[str, str]]: ...
    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None: ...
    @property
    def path(self) -> str: ...


# =====================================================
# REPOSITORIO CSV (ESTADO PARA MERGE)
# =====================================================

class CsvRepository(Repository):
    def __init__(self, path: str):
        self._path = path

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> Dict[str, Dict[str, str]]:
        if not os.path.exists(self._path):
            return {}

        rows: Dict[str, Dict[str, str]] = {}
        with open(self._path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                if not row:
                    continue
                rid = str(row.get("id_record", "")).strip()
                if rid:
                    rows[rid] = row
        return rows

    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS)
            w.writeheader()
            for _, row in sorted(rows_by_id.items(), key=lambda kv: str(kv[0])):
                out_row = {c: row.get(c, "") for c in CSV_COLS}
                w.writerow(out_row)


# =====================================================
# REPOSITORIO CONDELPI (PUBLICA DELTA + IMPRIME RESPUESTA)
# =====================================================

class CondelpiRepository(Repository):
    """
    Repo destino:
    - load(): vacío (Condelpi no se usa para merge)
    - save(): publica SOLO filas nuevas/actualizadas (delta)
    """

    def __init__(self, client: CondelpiClient):
        self.client = client
        self.translator = CondelpiPayloadTranslator()
        self._path = "condelpi://REVENTAS9"

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> Dict[str, Dict[str, str]]:
        return {}

    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None:
        total = len(rows_by_id)
        ok = 0
        fail = 0

        for i, (rid, row) in enumerate(rows_by_id.items(), start=1):
            payload = self.translator.build_payload(row)

            try:
                # 👉 llamada a la API
                resp = self.client.enviar_reventa(payload)

                ok += 1
                print(f"\n✅ [{i}/{total}] CONDELPI OK | id_record={rid}")
                print("📤 Payload enviado:")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                print("📨 Respuesta API Condelpi:")
                print(json.dumps(resp, indent=2, ensure_ascii=False))

            except Exception as e:
                fail += 1
                print(f"\n❌ [{i}/{total}] CONDELPI FAIL | id_record={rid}")
                print("📤 Payload enviado:")
                print(json.dumps(payload, indent=2, ensure_ascii=False))
                print("📛 Error:")
                print(str(e))

        print(f"\n📊 RESUMEN CONDELPI => OK={ok} FAIL={fail} TOTAL={total}")


# =====================================================
# REPOSITORIO COMPUESTO (CSV + CONDELPI, SIN TOCAR App)
# =====================================================

class CompositeRepository(Repository):
    """
    Repo compuesto:
    - load() => estado desde CSV
    - save(delta) =>
        1) carga estado
        2) aplica delta
        3) guarda estado completo en CSV
        4) publica delta a Condelpi (con impresión de respuesta)
    """

    def __init__(self, state_repo: CsvRepository, sink_repo: CondelpiRepository):
        self.state_repo = state_repo
        self.sink_repo = sink_repo
        self._path = f"{state_repo.path} + {sink_repo.path}"

    @property
    def path(self) -> str:
        return self._path

    def load(self) -> Dict[str, Dict[str, str]]:
        return self.state_repo.load()

    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None:
        if not rows_by_id:
            print("ℹ️ Delta vacío, nada que guardar ni publicar.")
            return

        # 1) estado actual
        merged = self.state_repo.load()

        # 2) aplicar delta
        for rid, row in rows_by_id.items():
            merged[str(rid)] = row

        # 3) guardar estado completo
        self.state_repo.save(merged)

        # 4) publicar SOLO delta
        self.sink_repo.save(rows_by_id)
