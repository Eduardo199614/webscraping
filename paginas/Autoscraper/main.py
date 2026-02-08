# paginas/Autoscraper/main.py
from __future__ import annotations
import argparse

# --------------------------------------------------
# (Opcional) cargar .env
# --------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from paginas.Autoscraper.app import App, AppConfig
from paginas.Autoscraper.dominio.politicas import ByDaysFreshnessPolicy
from paginas.Autoscraper.dominio.servicios import MergeService
from paginas.Autoscraper.dominio.modelo import ANIOS_OBJETIVO

# --------------------------------------------------
# IMPORTS SEGUROS DE TRADUCTORES
# --------------------------------------------------
from paginas.Autoscraper.infraestructura.traductor import AutocorRecordTranslator

try:
    from paginas.Autoscraper.infraestructura.traductor import PatioTuercaRecordTranslator
except Exception:
    PatioTuercaRecordTranslator = None

# --------------------------------------------------
# REPOSITORIOS
# --------------------------------------------------
from paginas.Autoscraper.infraestructura.repositorio import (
    CsvRepository,
    CondelpiRepository,
    CompositeRepository,
)

# --------------------------------------------------
# CLIENTES API
# --------------------------------------------------
from paginas.Autoscraper.infraestructura.api_cliente import RequestsApiClient
from paginas.Autoscraper.infraestructura.api_cliente_PatioTuerca import (
    PatioTuercaClientAdapter,
    RequestsWebClient,
)

from paginas.Autoscraper.infraestructura.AutosBDD.Api_Condelpi import (
    CondelpiConfig,
    CondelpiClient,
)


# ==================================================
# ARGUMENTOS
# ==================================================
def parse_args() -> tuple[AppConfig, str, str]:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--source",
        choices=["autocor", "patiotuerca"],
        default="autocor",
        help="Fuente de datos",
    )

    ap.add_argument(
        "--sink",
        choices=["csv", "condelpi"],
        default="csv",
        help="Destino: csv o condelpi",
    )

    ap.add_argument("--base-url", default=None)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--fresh-days", type=int, default=1)
    ap.add_argument("--user-agent", default="Mozilla/5.0 Autoscraper/1.0")

    args = ap.parse_args()

    BASE_URLS = {
        "autocor": "https://www.autocor.com.ec/api/listPilot",
        "patiotuerca": "https://ecuador.patiotuerca.com/usados/-/autos",
    }

    cfg = AppConfig(
        base_url=args.base_url or BASE_URLS[args.source],
        out_csv=f"datos/{args.source}_fichas.csv",
        timeout=args.timeout,
        retries=args.retries,
        fresh_days=max(0, int(args.fresh_days)),
        user_agent=args.user_agent,
    )

    return cfg, args.source, args.sink


# ==================================================
# MAIN
# ==================================================
def main() -> None:
    cfg, source, sink = parse_args()

    # -------------------------
    # FUENTE DE DATOS
    # -------------------------
    if source == "autocor":
        api = RequestsApiClient(
            base_url=cfg.base_url,
            user_agent=cfg.user_agent,
            timeout=cfg.timeout,
            retries=cfg.retries,
        )
        translator = AutocorRecordTranslator()
        merger = MergeService(ByDaysFreshnessPolicy(cfg.fresh_days))

    elif source == "patiotuerca":
        if PatioTuercaRecordTranslator is None:
            raise RuntimeError(
                "PatioTuercaRecordTranslator no existe en infraestructura/traductor.py"
            )

        web_client = RequestsWebClient(
            user_agent=cfg.user_agent,
            timeout=cfg.timeout,
        )
        api = PatioTuercaClientAdapter(
            web_client,
            anios=ANIOS_OBJETIVO,
        )
        translator = PatioTuercaRecordTranslator()
        merger = MergeService(ByDaysFreshnessPolicy(cfg.fresh_days))

    else:
        raise RuntimeError(f"Source no soportado: {source}")

    # -------------------------
    # DESTINO
    # -------------------------
    if sink == "csv":
        repo = CsvRepository(cfg.out_csv)

    else:
        c_cfg = CondelpiConfig.from_env(
            timeout=cfg.timeout,
            retries=cfg.retries,
        )
        c_client = CondelpiClient(c_cfg)

        state_repo = CsvRepository(cfg.out_csv)
        sink_repo = CondelpiRepository(c_client)

        repo = CompositeRepository(state_repo, sink_repo)

    # -------------------------
    # EJECUTAR
    # -------------------------
    app = App(
        api=api,
        translator=translator,
        repo=repo,
        merger=merger,
    )
    app.run()


if __name__ == "__main__":
    main()
