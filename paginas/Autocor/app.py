# autocor_solid/app.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class AppConfig:
    base_url: str
    out_csv: str
    timeout: int
    retries: int
    fresh_days: int
    user_agent: str

class App:
    def __init__(self, api, translator, repo, merger):
        self.api = api
        self.translator = translator
        self.repo = repo
        self.merger = merger

    def run(self) -> None:
        # 1) Obtener entidades (JSON o scrapping, según el cliente)
        if hasattr(self.api, "fetch_all"):
            entities = self.api.fetch_all()
        else:
            # compatibilidad si se usa ApiClient de Autocor con discover_first_page()
            page_count, entities = self.api.discover_first_page()
            for p in range(2, page_count + 1):
                entities.extend(self.api.fetch_page(p))

        # 2) Traducir a filas CSV
        incoming_rows = [self.translator.build_csv_row(e) for e in entities]

        # 3) Fusionar con CSV existente
        existing = self.repo.load()
        merged, metrics = self.merger.merge(existing, incoming_rows)

        # 4) Guardar
        self.repo.save(merged)

        print(
            f"✓ Merge completado → Total filas: {metrics['total']} | "
            f"Conservadas vigentes: {metrics['kept']} | "
            f"Actualizadas: {metrics['updated']} | Nuevas: {metrics['added']}"
        )
        print(f"✓ CSV: {self.repo.path}")
