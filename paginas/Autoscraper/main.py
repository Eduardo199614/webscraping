# autocor_solid/main.py
from __future__ import annotations
import argparse, os, sys
# Importaciones de Autoscraper (ajustadas para la estructura del proyecto)
from Autoscraper.app import App, AppConfig
from Autoscraper.dominio.politicas import ByDaysFreshnessPolicy
from Autoscraper.dominio.servicios import MergeService
from Autoscraper.infraestructura.repositorio import CsvRepository # Usaremos CSV para el merge
from Autoscraper.dominio.modelo import CSV_COLS # Usaremos el modelo simple

# Importaciones de la lógica específica de PatioTuerca
# NOTA: Debes asegurarte que las rutas relativas o absolutas a Autocor son correctas
try:
    # Asumimos que los archivos de Autocor son accesibles
    from paginas.Autocor.infraestructura.api_client_PatioTuerca import (
        RequestsWebClient, 
        PatioTuercaClientAdapter
    )
    from paginas.Autocor.infraestructura.traductor import PatioTuercaRecordTranslator
    from paginas.Autocor.dominio.modelo import ANIOS_OBJETIVO # Lote de Años
except ImportError as e:
    print(f"Error de importación de componentes de PatioTuerca. Verifica las rutas: {e}")
    sys.exit(1)


def parse_args() -> AppConfig:
    ap = argparse.ArgumentParser(description="Ejecutor de Web Scraping por lotes (años) de PatioTuerca.")
    
    # Parámetros necesarios para el scraping
    ap.add_argument("--out-csv", 
                    default=os.path.join(os.getcwd(), "datos", "PatioTuerca", "vehiculos_pt_lotes.csv"),
                    help="Ruta del archivo CSV de salida.")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoscraperPT/1.0")
    
    # Parámetros para la política de vigencia del MergeService
    ap.add_argument("--fresh-days", type=int, default=7,
                    help="Días de vigencia del registro en el CSV.")

    args = ap.parse_args()
    
    return AppConfig(
        base_url="", # Ya no se usa para PatioTuerca
        out_csv=args.out_csv,
        timeout=args.timeout,
        retries=1, # No aplica la lógica de reintentos paginados de la API
        fresh_days=max(0, int(args.fresh_days)),
        user_agent=args.user_agent,
    )

def main() -> None:
    cfg = parse_args()
    
    # ------------------------------------------------------------------
    # 1. Componentes de INFRAESTRUCTURA (PatioTuerca y Persistencia CSV)
    # ------------------------------------------------------------------
    
    # Cliente Web: Necesario para el adaptador de PatioTuerca
    web_client = RequestsWebClient(
        user_agent=cfg.user_agent, 
        timeout=cfg.timeout
    )
    
    # Adaptador del Scraper: Define el lote de entrada (ANIOS_OBJETIVO)
    # El Adapter hace el trabajo de obtener la lista de vehículos para TODOS los años en el lote.
    api = PatioTuercaClientAdapter(
        web_client=web_client, 
        anios=ANIOS_OBJETIVO 
    )
    
    # Traductor: Convierte el objeto Vehiculo a un diccionario plano para CSV
    translator = PatioTuercaRecordTranslator()

    # Repositorio: Usaremos el CSV para cargar y guardar el lote (MergeService necesita el lote completo)
    repo = CsvRepository(path=cfg.out_csv)

    # ------------------------------------------------------------------
    # 2. Componentes de DOMINIO
    # ------------------------------------------------------------------
    
    # Política de Vigencia: Se aplica al cargar el lote existente
    freshness = ByDaysFreshnessPolicy(fresh_days=cfg.fresh_days)
    merger = MergeService(freshness=freshness)

    # ------------------------------------------------------------------
    # 3. Ejecución de la Aplicación (El Batching Secuencial)
    # ------------------------------------------------------------------

    # Usamos la App de Autocor, pero 'api' es nuestro PatioTuercaClientAdapter
    app = App(api=api, translator=translator, repo=repo, merger=merger)
    
    print(f"--- 🚀 Ejecutando Batch Secuencial para años: {ANIOS_OBJETIVO} ---")
    print(f"📦 Guardando lote final en: {cfg.out_csv}")
    print(f"⏳ Vigencia de registros: {cfg.fresh_days} días")

    # Ejecuta el flujo: Obtener (Batch Años) -> Traducir -> Merge (Batch Existente) -> Guardar
    app.run()


if __name__ == "__main__":
    main()