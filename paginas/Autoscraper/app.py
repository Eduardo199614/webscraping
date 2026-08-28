# app.py (o donde tengas tu clase App)
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
    def __init__(self, api, translator, repo, merger, publisher=None):
        self.api = api
        self.translator = translator
        self.repo = repo
        self.merger = merger
        self.publisher = publisher

    def _publish_delta(self, delta_rows: list[dict], fuente: str) -> None:
        if not self.publisher:
            return
        if not delta_rows:
            return

        res = self.publisher.publish(delta_rows, fuente=fuente)
        print(f"  ☁ CONDELPI: enviados={res.get('enviados')} fallidos={res.get('fallidos')}")
        if res.get("fallidos"):
            print(f"  ⚠ Ejemplo fallo: {res['detalle_fallidos'][0]}")

    def run(self) -> None:
        """
        Ejecuta el proceso con batching:
        - Autocor: lote por página.
        - PatioTuerca: lote por año.
        - Otros: modo monolítico (compatibilidad).
        """
        if hasattr(self.api, "fetch_year") and hasattr(self.api, "anios"):
            self._run_patiotuerca_by_year()
        elif hasattr(self.api, "discover_first_page") and hasattr(self.api, "fetch_page"):
            self._run_autocor_by_page()
        elif hasattr(self.api, "fetch_all"):
            self._run_monolithic()
        else:
            raise RuntimeError("API no compatible con App.run()")

    # -----------------------
    #  MODO BATCH: PATIOTUERCA
    # -----------------------
    def _run_patiotuerca_by_year(self) -> None:
        print("▶ Ejecutando en modo batch por año (PatioTuerca)")

        merged = self.repo.load()
        total_metrics = {"kept": 0, "updated": 0, "added": 0}

        for anio in self.api.anios:
            print(f"\n📆 Procesando año {anio}...")
            entities = self.api.fetch_year(anio)

            if not entities:
                print(f"  (sin resultados para {anio})")
                continue

            incoming_rows = [self.translator.build_csv_row(e) for e in entities]
            merged, metrics, delta = self.merger.merge(merged, incoming_rows)

            for k in ("kept", "updated", "added"):
                total_metrics[k] += metrics.get(k, 0)

            # Guardar delta (como ya lo haces)
            self.repo.save(merged)

            # ✅ NUEVO: enviar delta a Condelpi
            self._publish_delta(delta, fuente="Patiotuerca")

            print(
                f"  ✓ Año {anio}: total_now={metrics['total']} | "
                f"kept={metrics['kept']} | updated={metrics['updated']} | added={metrics['added']} | "
                f"delta={len(delta)}"
            )
            print(f"  ✓ Salida parcial en: {self.repo.path}")

        total = len(merged)
        print(
            f"\n✓ Merge completado (todos los años) → Total filas: {total} | "
            f"Conservadas vigentes: {total_metrics['kept']} | "
            f"Actualizadas: {total_metrics['updated']} | "
            f"Nuevas: {total_metrics['added']}"
        )
        print(f"✓ Salida final: {self.repo.path}")

    # -----------------------
    #  MODO BATCH: AUTOCOR
    # -----------------------
    def _run_autocor_by_page(self) -> None:
        print("▶ Ejecutando en modo batch por página (Autocor)")

        merged = self.repo.load()
        total_metrics = {"kept": 0, "updated": 0, "added": 0}

        page_count, entities_page1 = self.api.discover_first_page()
        print(f"  📄 Total de páginas reportadas: {page_count}")

        pages = [(1, entities_page1)]
        for p in range(2, page_count + 1):
            pages.append((p, self.api.fetch_page(p)))

        for page_num, page_entities in pages:
            print(f"\n📄 Procesando página {page_num}/{page_count}...")

            if not page_entities:
                print("  (página vacía)")
                continue

            incoming_rows = [self.translator.build_csv_row(e) for e in page_entities]
            merged, metrics, delta = self.merger.merge(merged, incoming_rows)

            for k in ("kept", "updated", "added"):
                total_metrics[k] += metrics.get(k, 0)

            self.repo.save(merged)

            # ✅ NUEVO: enviar delta a Condelpi
            self._publish_delta(delta, fuente="Autocor")

            print(
                f"  ✓ Página {page_num}: total_now={metrics['total']} | "
                f"kept={metrics['kept']} | updated={metrics['updated']} | added={metrics['added']} | "
                f"delta={len(delta)}"
            )
            print(f"  ✓ Salida parcial en: {self.repo.path}")

        total = len(merged)
        print(
            f"\n✓ Merge completado (todas las páginas) → Total filas: {total} | "
            f"Conservadas vigentes: {total_metrics['kept']} | "
            f"Actualizadas: {total_metrics['updated']} | "
            f"Nuevas: {total_metrics['added']}"
        )
        print(f"✓ Salida final: {self.repo.path}")

    # -----------------------
    #  MODO MONOLÍTICO
    # -----------------------
    def _run_monolithic(self) -> None:
        if hasattr(self.api, "fetch_all"):
            entities = self.api.fetch_all()
        else:
            page_count, entities = self.api.discover_first_page()
            for p in range(2, page_count + 1):
                entities.extend(self.api.fetch_page(p))

        incoming_rows = [self.translator.build_csv_row(e) for e in entities]

        existing = self.repo.load()
        merged, metrics, delta = self.merger.merge(existing, incoming_rows)

        self.repo.save(merged)

        # ✅ NUEVO: enviar delta a Condelpi
        self._publish_delta(delta, fuente="Monolithic")

        print(
            f"✓ Merge completado → Total: {metrics['total']} | "
            f"kept={metrics['kept']} | updated={metrics['updated']} | added={metrics['added']} | "
            f"delta={len(delta)}"
        )
        print(f"✓ Salida: {self.repo.path}")
