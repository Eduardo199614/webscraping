# autocor_solid/domain/services.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Iterable, Tuple, List
from .politicas import FreshnessPolicy
from .modelo import now_utc

# patioTuerca_solid/domain/services.py

@dataclass
class MergeService:
    freshness: FreshnessPolicy

    def merge(
        self,
        existing: Dict[str, Dict[str, str]],
        incoming_rows: Iterable[Dict[str, Any]],
        id_field: str = "id_record"
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
        """Funde datasets aplicando FreshnessPolicy; devuelve (merged, métricas)."""
        ref = now_utc()
        merged = dict(existing)
        kept = updated = added = 0

        for row in incoming_rows:
            key = str(row.get(id_field, "")).strip()
            if not key:
                # Sin id: no aplica policy; igual se incorpora
                phantom_key = f"__NOID__{id(row)}"
                merged[phantom_key] = row
                added += 1
                continue

            if key in existing:
                if self.freshness.is_fresh(existing[key], ref):
                    kept += 1
                else:
                    merged[key] = row
                    updated += 1
            else:
                merged[key] = row
                added += 1

        metrics = {"kept": kept, "updated": updated, "added": added, "total": len(merged)}
        return merged, metrics

#Patio Tuerca--------------------------------------------------
import pandas as pd
from datetime import datetime

@dataclass
class FichaMergeService:
    """Servicio de dominio: compara fichas nuevas con el histórico y aplica reglas de actualización."""

    def merge(
        self,
        historico: pd.DataFrame,
        nuevas: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Devuelve el nuevo histórico actualizado según cambios detectados.
        """
        if historico.empty:
            df_final = nuevas.copy()
            metrics = {"added": len(nuevas), "updated": 0, "kept": 0, "total": len(df_final)}
            return df_final, metrics

        df_final = historico.copy()
        added = updated = kept = 0

        for _, nuevo in nuevas.iterrows():
            id_auto = nuevo["ID"]
            if id_auto in df_final["ID"].values:
                activo = df_final[
                    (df_final["ID"] == id_auto) & (df_final["VIGENCIA"] == "Activo")
                ]
                if not activo.empty:
                    actual = activo.iloc[-1]
                    cambiado = any(
                        nuevo[c] != actual[c]
                        for c in ["AÑO", "PRECIO", "MARCA", "MODELO", "KILOMETRAJE", "MOTOR", "TRANSMISION"]
                    )
                    if cambiado:
                        df_final.loc[activo.index, "VIGENCIA"] = "No activo"
                        df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
                        updated += 1
                    else:
                        kept += 1
                else:
                    df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
                    added += 1
            else:
                df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
                added += 1

        metrics = {"added": added, "updated": updated, "kept": kept, "total": len(df_final)}
        return df_final, metrics