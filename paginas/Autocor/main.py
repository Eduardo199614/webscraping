# autocor_solid/main.py
from __future__ import annotations
import argparse, os
from Autocor.app import App, AppConfig
from Autocor.infraestructura.api_cliente import RequestsApiClient,DEFAULT_BASE_URL
from Autocor.infraestructura.api_cliente_PatioTuerca import RequestsApiClientPT
from Autocor.infraestructura.traductor import AutocorRecordTranslator
from Autocor.infraestructura.traductor import PatioTuercaRecordTranslator
from Autocor.infraestructura.repositorio import CsvRepository
from Autocor.infraestructura.repositorio_sp import SqlServerStoredProcRepository
from Autocor.dominio.politicas import ByDaysFreshnessPolicy
from Autocor.dominio.servicios import MergeService
from Autocor.dominio.servicios import FichaMergeService
from Autocor.dominio.politicas import ByDaysFreshnessPolicy
from Autocor.dominio.servicios import MergeService

def parse_args() -> AppConfig:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["autocor", "patiotuerca"], default="autocor",
                    help="Fuente de datos a procesar")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--fresh-days", type=int, default=1,
                    help="Días de vigencia (se envía al SP)")
    ap.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Scraper/1.0")
    args = ap.parse_args()

    # Base URLs por fuente
    BASE_URLS = {
        "autocor": "https://api.autocor.com/api/cars",
        "patiotuerca": "https://www.patiotuerca.com/api/autos"
    }

    return AppConfig(
        base_url=args.base_url or BASE_URLS[args.source],
        out_csv=f"{args.source}_fichas.csv",
        timeout=args.timeout,
        retries=args.retries,
        fresh_days=max(0, int(args.fresh_days)),
        user_agent=args.user_agent,
    ), args.source

def main() -> None:
    cfg, source = parse_args()

    api = RequestsApiClient(
        base_url=cfg.base_url,
        user_agent=cfg.user_agent,
        timeout=cfg.timeout,
        retries=cfg.retries,
    )

    # Seleccionar traductor según la fuente
    if source == "autocor":
        translator = AutocorRecordTranslator()
        proc_name = "dbo.sp_Autocor_UpsertFromJson"
    else:
        translator = PatioTuercaRecordTranslator()
        proc_name = "dbo.sp_PatioTuerca_UpsertFromJson"

    # Configuración de conexión
    conn_str = os.environ.get(
        "MSSQL_CONN",
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.0.131.75\\Originarsa;DATABASE=BD_AUTOCOR;UID=usr;PWD=***;Encrypt=Yes;TrustServerCertificate=Yes"
    )

    repo = SqlServerStoredProcRepository(
        conn_str=conn_str,
        proc_name=proc_name,
        fresh_days=cfg.fresh_days
    )

    freshness = ByDaysFreshnessPolicy(fresh_days=0)
    merger = MergeService(freshness=freshness)

    app = App(api=api, translator=translator, repo=repo, merger=merger)
    app.run()

if __name__ == "__main__":
    main()
