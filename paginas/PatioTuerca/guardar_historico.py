import pandas as pd
import os

ARCHIVO_PARQUET = "fichas_autos.parquet"
ARCHIVO_CSV = "fichas_autos.csv"


def actualizar_historico(datos_nuevos):
    """
    Actualiza el histórico con los datos ya limpios.
    Recibe una lista de diccionarios (JSON) en lugar de un DataFrame.
    """
    # Convertimos la lista de diccionarios a DataFrame
    df_nuevos = pd.DataFrame(datos_nuevos)

    if os.path.exists(ARCHIVO_PARQUET):
        df_hist = pd.read_parquet(ARCHIVO_PARQUET)
    else:
        df_hist = pd.DataFrame()

    if df_hist.empty:
        df_final = df_nuevos
    else:
        df_final = df_hist.copy()
        for _, nuevo in df_nuevos.iterrows():
            id_auto = nuevo["ID"]
            if id_auto in df_final["ID"].values:
                activo = df_final[(df_final["ID"] == id_auto) & (df_final["VIGENCIA"] == "Activo")]
                if not activo.empty:
                    actual = activo.iloc[-1]
                    cambiado = any(
                        nuevo[c] != actual[c]
                        for c in ["AÑO", "PRECIO", "MARCA", "MODELO", "KILOMETRAJE", "MOTOR", "TRANSMISION"]
                    )
                    if cambiado:
                        df_final.loc[activo.index, "VIGENCIA"] = "No activo"
                        df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
                else:
                    df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)
            else:
                df_final = pd.concat([df_final, pd.DataFrame([nuevo])], ignore_index=True)

    # Guardamos resultados
    df_final.to_parquet(ARCHIVO_PARQUET, index=False)
    df_final.to_csv(ARCHIVO_CSV, index=False, encoding="utf-8-sig")

    print(f"\n💾 Histórico actualizado: {len(df_final)} registros totales.")
    return df_final


# ================================================================
# 4️⃣ PARTE: EJECUCIÓN PRINCIPAL
# ================================================================
if __name__ == "__main__":
    urls = [
        "https://ecuador.patiotuerca.com/vehicle/autos-kia-k3_x-line-guayaquil-2025/1935036",
    ]
    

