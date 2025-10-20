# main.py
from paginas.PatioTuerca.extraer_urls import extraer_multiples_anios
from paginas.PatioTuerca.extraer_fichas import extraer_fichas_desde_lista
from paginas.PatioTuerca.guardar_historico import actualizar_historico
if __name__ == "__main__":
    print("\n🚗 Iniciando scraping completo...\n")

    # Paso 1: obtener todas las URLs
    anios_a_buscar = [2015,2016,2017,2018,2019,2020]
    urls = extraer_multiples_anios(anios_a_buscar,num_paginas=5, pausa=2)

    print(f"\n🔹 Proceso inicial completado. Total de URLs encontradas: {len(urls)}\n")

    # Paso 2: extraer fichas técnicas y guardar en JSON
    resultados = extraer_fichas_desde_lista(urls, pausa = 5)
    
    print(f"\n🏁 Proceso 2 completado. {len(resultados)} fichas guardadas exitosamente.")

    # Paso 3: actualizar histórico (vigencia, duplicados, cambios)
    df = actualizar_historico(resultados)
    
    print(f"\n🏁 Proceso final completado. Total registros actuales: {len(df)}")