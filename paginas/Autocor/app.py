# autocor_solid/app.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict, Any, Iterable, Tuple, List
from .dominio.servicios import MergeService
from .infraestructura.api_cliente import ApiClient
from .infraestructura.repositorio import Repository
from .infraestructura.traductor import RecordTranslator

@dataclass
class AppConfig:
    base_url: str
    out_csv: str
    timeout: int
    retries: int
    fresh_days: int
    user_agent: str

class App:
    """Orquesta: API → traducir → merge → guardar"""
    def __init__(self, api: ApiClient, translator: RecordTranslator, repo: Repository, merger: MergeService):
        self.api = api
        self.translator = translator
        self.repo = repo
        self.merger = merger

    def run(self) -> None:
        # 1) Descubrir páginas y obtener page 1
        page_count, entities = self.api.discover_first_page()

        # 2) Resto de páginas
        for p in range(2, page_count + 1):
            entities.extend(self.api.fetch_page(p))

        # 3) Traducir a filas CSV mínimas
        incoming_rows = [self.translator.build_csv_row(e) for e in entities]

        # 4) Cargar existente y fusionar
        existing = self.repo.load()
        merged, metrics = self.merger.merge(existing, incoming_rows)

        # 5) Guardar
        self.repo.save(merged)

        print(
            f"✓ Merge completado → Total filas: {metrics['total']} | "
            f"Conservadas vigentes: {metrics['kept']} | "
            f"Actualizadas: {metrics['updated']} | Nuevas: {metrics['added']}"
        )
        print(f"✓ CSV: {self.repo.path}")
