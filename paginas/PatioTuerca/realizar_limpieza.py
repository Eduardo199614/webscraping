#para probar este archivo importar la función extraer_fichas_desde_lista desde extraer_fichas.py
from extraer_fichas import extraer_fichas_desde_lista
from guardar_historico import actualizar_historico
import pandas as pd
import re
from datetime import datetime
import json
def limpiar_valor_numerico(valor):
    if pd.isna(valor):
        return None
    valor = re.sub(r"[^0-9,.\-]", "", str(valor))
    valor = valor.replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def limpiar_kilometraje(valor):
    num = limpiar_valor_numerico(valor)
    return int(num) if num is not None else None


def limpiar_motor(valor):
    num = limpiar_valor_numerico(valor)
    if num is None:
        return None
    if num < 10:
        return int(num * 1000)
    return int(num)


def limpiar_precio(valor):
    num = limpiar_valor_numerico(valor)
    if num < 1000:
        num *= 1000
    return round(num, 2) if num is not None else None


def normalizar_vigencia(v):
    if isinstance(v, str):
        v = v.strip().capitalize()
        return "Activo" if v.lower().startswith("a") else "No activo"
    return "No activo"


def limpiar_resultados(resultados):
    """Convierte la lista de resultados en un DataFrame limpio y homogéneo."""
    filas = []
    for r in resultados:
        if not r.get("Data"):
            continue
        fila = {
            "ID": r["ID"],
            "AÑO": r["Data"].get("Año"),
            "PRECIO": limpiar_precio(r["Data"].get("Precio")),
            "MARCA": (r["Data"].get("Marca") or "").strip().upper(),
            "MODELO": (r["Data"].get("Modelo") or "").strip().upper(),
            "KILOMETRAJE": limpiar_kilometraje(r["Data"].get("Kilometraje")),
            "MOTOR": limpiar_motor(r["Data"].get("Motor(cilindraje)")),
            "TRANSMISION": (r["Data"].get("Transmisión") or "").strip().upper(),
            "FECHA_INGRESO": datetime.strptime(r["FechaIngreso"], "%Y-%m-%d %H:%M:%S").date(),
            "VIGENCIA": normalizar_vigencia(r["Vigencia"]),
        }
        filas.append(fila)
    return filas

if __name__ == "__main__":
    urls = [
        "https://ecuador.patiotuerca.com/vehicle/autos-kia-sonet-quito-2025/1925019",
        # puedes agregar más URLs aquí
    ]

    resultados = extraer_fichas_desde_lista(urls)
    print(resultados)
    df_limpio = limpiar_resultados(resultados)
    print(df_limpio)
    df_historico = actualizar_historico(df_limpio)
    print("\n✅ Proceso completo: extracción → limpieza → guardado histórico.")