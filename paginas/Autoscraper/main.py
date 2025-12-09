# autocor_solid/main.py
from __future__ import annotations
import argparse, os
from dataclasses import dataclass
from paginas.Autoscraper.app import App, AppConfig
from paginas.Autoscraper.dominio.politicas import ByDaysFreshnessPolicy
from paginas.Autoscraper.dominio.servicios import MergeService
from paginas.Autoscraper.dominio.modelo import ANIOS_OBJETIVO
from paginas.Autoscraper.infraestructura.traductor import (
    AutocorRecordTranslator,
    PatioTuercaRecordTranslator,
)
from paginas.Autoscraper.infraestructura.repositorio import CsvRepository
from paginas.Autoscraper.infraestructura.api_cliente import RequestsApiClient, DEFAULT_BASE_URL
from paginas.Autoscraper.infraestructura.api_cliente_PatioTuerca import (
    PatioTuercaClientAdapter,
    RequestsWebClient,
)

# -------------------------
# Configuración general
# -------------------------


def parse_args() -> tuple[AppConfig, str]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["autocor", "patiotuerca"], default="autocor",
                    help="Fuente de datos a procesar")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--fresh-days", type=int, default=1,
                    help="Días de vigencia de datos (para políticas de merge)")
    ap.add_argument("--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Scraper/1.0")

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

    return cfg, args.source


# -------------------------
# Ejecución principal
# -------------------------

def main() -> None:
    cfg, source = parse_args()

    # Selección de componentes según la fuente
    if source == "autocor":
        # --- AUTOCOR ---
        api = RequestsApiClient(
            base_url=cfg.base_url,
            user_agent=cfg.user_agent,
            timeout=cfg.timeout,
            retries=cfg.retries,
        )
        translator = AutocorRecordTranslator()
        merger = MergeService(ByDaysFreshnessPolicy(cfg.fresh_days))

    else:
        # --- PATIOTUERCA ---
        web_client = RequestsWebClient(user_agent=cfg.user_agent, timeout=cfg.timeout)
        # años a scrapear → ajustable en modelo
        api = PatioTuercaClientAdapter(web_client, anios=ANIOS_OBJETIVO)
        translator = PatioTuercaRecordTranslator()
        merger = MergeService(ByDaysFreshnessPolicy(cfg.fresh_days))

    # Repositorio en CSV 
    repo = CsvRepository(cfg.out_csv)

    # Crear app y ejecutar
    app = App(api=api, translator=translator, repo=repo, merger=merger)
    app.run()


if __name__ == "__main__":
    main()
