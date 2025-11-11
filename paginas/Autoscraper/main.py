# autocor_solid/main.py
from __future__ import annotations
import argparse, os
from Autocor.app import App, AppConfig
from Autocor.infraestructura.api_cliente import RequestsApiClient,DEFAULT_BASE_URL
from Autocor.infraestructura.traductor import AutocorRecordTranslator
from Autocor.infraestructura.repositorio import CsvRepository
from Autocor.infraestructura.repositorio_sp import SqlServerStoredProcRepository
from Autocor.dominio.politicas import ByDaysFreshnessPolicy
from Autocor.dominio.servicios import MergeService
from Autocor.dominio.politicas import ByDaysFreshnessPolicy
from Autocor.dominio.servicios import MergeService

def parse_args() -> AppConfig:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--fresh-days", type=int, default=1,
                    help="Días de vigencia (se envía al SP)")
    ap.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutocorScraper/1.0")
    args = ap.parse_args()
    # out-csv ya no es necesario cuando usas SP, pero puedes dejar AppConfig igual si quieres
    return AppConfig(
        base_url=args.base_url,
        out_csv="",  # no se usa con SP
        timeout=args.timeout,
        retries=args.retries,
        fresh_days=max(0, int(args.fresh_days)),
        user_agent=args.user_agent,
    )

def main() -> None:
    cfg = parse_args()

    api = RequestsApiClient(
        base_url=cfg.base_url,
        user_agent=cfg.user_agent,
        timeout=cfg.timeout,
        retries=cfg.retries,
    )
    translator = AutocorRecordTranslator()

    conn_str = os.environ.get(
        "MSSQL_CONN",
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER=10.0.131.75\\Originarsa;DATABASE=BD_AUTOCOR;UID=usr;PWD=***;Encrypt=Yes;TrustServerCertificate=Yes"
    )
    repo = SqlServerStoredProcRepository(
        conn_str=conn_str,
        proc_name="dbo.sp_Autocor_UpsertFromJson",
        fresh_days=cfg.fresh_days
    )

    # Política a 0 días → MergeService no conserva nada; manda todo al SP
    freshness = ByDaysFreshnessPolicy(fresh_days=0)
    merger = MergeService(freshness=freshness)

    app = App(api=api, translator=translator, repo=repo, merger=merger)
    app.run()

if __name__ == "__main__":
    main()
