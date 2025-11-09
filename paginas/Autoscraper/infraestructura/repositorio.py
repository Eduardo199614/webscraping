# autocor_solid/infra/repositories.py
from __future__ import annotations
import os, csv
from typing import Protocol, Dict, Any
from ..dominio.modelo import CSV_COLS

class Repository(Protocol):
    def load(self) -> Dict[str, Dict[str, str]]: ...
    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None: ...
    @property
    def path(self) -> str: ...

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
                key = str(row.get("id_record", "")).strip()
                if key:
                    rows[key] = row
        return rows

    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLS)
            w.writeheader()
            for _, row in sorted(rows_by_id.items(), key=lambda kv: str(kv[0])):
                out_row = {c: row.get(c, "") for c in CSV_COLS}
                w.writerow(out_row)
