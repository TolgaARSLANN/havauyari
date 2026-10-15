"""Panonun kullandığı tahmin servisini oluşturan fabrika (testlerde değiştirilebilir)."""

from __future__ import annotations

from collections.abc import Callable

from havauyari.serving.service import ForecastService


def _default_factory() -> ForecastService:
    from havauyari.serving.data import LiveProvider
    from havauyari.serving.service import default_repository, load_artifacts

    # DATABASE_URL tanımlıysa pano da tahminleri API ile aynı veritabanına yazar/okur
    return ForecastService(load_artifacts(), LiveProvider(), repository=default_repository())


SERVICE_FACTORY: Callable[[], ForecastService] = _default_factory
