# Autocor/infraestructura/repositorio_sp.py
from __future__ import annotations
import json, pyodbc
from typing import Dict, Any

class SqlServerStoredProcRepository:
    """
    Repository que persiste vía SP:
      - load(): opcional; puedes implementarlo si necesitas leer todo.
      - save(rows_by_id): serializa a JSON y ejecuta el SP.
    """
    def __init__(
        self,
        conn_str: str,
        proc_name: str = "dbo.sp_Autocor_UpsertFromJson",
        fresh_days: int = 1
    ):
        self._conn_str = conn_str
        self._proc_name = proc_name
        self._fresh_days = fresh_days

    @property
    def path(self) -> str:
        return f"mssql://{self._proc_name}"

    def load(self) -> Dict[str, Dict[str, str]]:
        # Si tu App/servicio ya no necesita leer antes de upsert,
        # puedes devolver {} y dejar que el SP decida.
        return {}

    def save(self, rows_by_id: Dict[str, Dict[str, Any]]) -> None:
        # Serializar a JSON array en el formato que espera el SP
        payload = json.dumps(list(rows_by_id.values()), ensure_ascii=False)

        with pyodbc.connect(self._conn_str) as conn:
            cur = conn.cursor()
            # Output params: usa variables locales para capturar
            sql = f"""
            DECLARE @kept INT, @updated INT, @inserted INT;
            EXEC {self._proc_name}
                @payload = ?,
                @fresh_days = ?,
                @kept = @kept OUTPUT,
                @updated = @updated OUTPUT,
                @inserted = @inserted OUTPUT;
            SELECT @kept AS kept, @updated AS updated, @inserted AS inserted;
            """
            cur.execute(sql, (payload, self._fresh_days))
            row = cur.fetchone()
            if row:
                print(f"SP → kept={row.kept} | updated={row.updated} | inserted={row.inserted}")
            conn.commit()
