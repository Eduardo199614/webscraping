# main.py
from extraer_urls import extraer_todas_las_paginas
from extraer_fichas import extraer_fichas_desde_lista

if __name__ == "__main__":
    print("\n🚗 Iniciando scraping completo...\n")

    # Paso 1: obtener todas las URLs
    urls = extraer_todas_las_paginas(num_paginas=1, pausa=2)

    print(f"\n🔹 Total de URLs encontradas: {len(urls)}\n")

    # Paso 2: extraer fichas técnicas y guardar en JSON
    resultados = extraer_fichas_desde_lista(
        urls,
        pausa=4,
        salida_json="fichas_autos.json"
    )

    print(f"\n🏁 Proceso completado. {len(resultados)} fichas guardadas exitosamente.")
