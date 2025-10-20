import pandas as pd
import os

ARCHIVO_PARQUET = "fichas_autos.parquet"
ARCHIVO_CSV = "fichas_autos.csv"


def actualizar_historico(resultados):
    """Actualiza el histórico con nuevos datos, manejando vigencia."""
    # Cargar histórico previo si existe
    if os.path.exists(ARCHIVO_PARQUET):
        df_hist = pd.read_parquet(ARCHIVO_PARQUET)
    else:
        df_hist = pd.DataFrame()

    # Convertir los nuevos resultados en DataFrame plano
    nuevos_registros = []
    for r in resultados:
        if not r.get("Data"):
            continue
        fila = {
            "ID": r["ID"],
            "FechaIngreso": r["FechaIngreso"],
            "Vigencia": r["Vigencia"],
            **r["Data"]
        }
        nuevos_registros.append(fila)

    df_nuevos = pd.DataFrame(nuevos_registros)

    if df_hist.empty:
        df_final = df_nuevos
    else:
        df_final = df_hist.copy()

        for _, nuevo in df_nuevos.iterrows():
            id_auto = nuevo["ID"]
            if id_auto in df_final["ID"].values:
                # Obtener último registro activo del mismo ID
                activo = df_final[(df_final["ID"] == id_auto) & (df_final["Vigencia"] == "Activo")]
                if not activo.empty:
                    actual = activo.iloc[-1]
                    # Comparar si hubo cambios en los campos
                    cambiado = any(
                        nuevo[c] != actual[c]
                        for c in nuevo.index if c not in ["ID", "FechaIngreso", "Vigencia"]
                    )
                    if cambiado:
                        df_final.loc[activo.index, "Vigencia"] = "No activo"
                        df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
                else:
                    # Si existe pero estaba inactivo, reactivarlo si coincide
                    df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
            else:
                # Nuevo ID nunca visto
                df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)

    # Guardar ambos formatos
    df_final.to_parquet(ARCHIVO_PARQUET, index=False)
    df_final.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8-sig")

    print(f"\n💾 Histórico actualizado: {len(df_final)} registros totales.")
    return df_final
