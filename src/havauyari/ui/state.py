"""Panonun kullandığı tahmin servisini oluşturan fabrika (testlerde değiştirilebilir)."""

from __future__ import annotations

from collections.abc import Callable

from havauyari.serving.service import ForecastService


def _default_factory() -> ForecastService:
    from havauyari.serving.data import LiveProvider
    from havauyari.serving.service import load_artifacts

    return ForecastService(load_artifacts(), LiveProvider())


SERVICE_FACTORY: Callable[[], ForecastService] = _default_factory
