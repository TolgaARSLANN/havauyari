"""HavaUyarı tahmin API'si (Faz 5.2).

Çalıştırma:
    uvicorn havauyari.serving.app:app --reload
    -> http://127.0.0.1:8000/docs

Uç noktalar:
    GET /health                 servis ve model durumu
    GET /stations               istasyonlar ve uyarı karar eşikleri
    GET /forecast/{station}     24 saat sonrası için tahmin, %80'lik aralık, uyarı, açıklama
    GET /alerts                 tüm istasyonlar (?only_alerts=true: yalnızca uyarı ya da uyarı
                                riski olanlar)
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from havauyari import __version__
from havauyari.serving.schemas import Forecast, Health, Station, StationError
from havauyari.serving.service import DataUnavailable, ForecastService

DESCRIPTION = (
    "Türkiye'deki hava kalitesi istasyonlarında **24 saat sonra ölçülecek PM2.5** değerinin "
    "tahmini. Tahminler; CAMS atmosfer modeli verileri, o gün yayımlanan hava tahmini ve "
    "istasyonun geçmiş ölçümleriyle eğitilmiş bir LightGBM modeliyle üretilir. Yalnızca "
    "bilgilendirme amaçlıdır; resmî uyarıların yerine geçmez."
)


def create_app(service: ForecastService | None = None) -> FastAPI:
    """`service` verilmezse ilk istekte gerçek model ve canlı veri sağlayıcıyla yüklenir."""
    app = FastAPI(title="HavaUyarı API", version=__version__, description=DESCRIPTION)
    state: dict = {"service": service, "error": None}

    def get_service() -> ForecastService:
        if state["service"] is None and state["error"] is None:
            try:
                from havauyari.serving.data import LiveProvider
                from havauyari.serving.service import load_artifacts

                state["service"] = ForecastService(load_artifacts(), LiveProvider())
            except FileNotFoundError as e:
                state["error"] = str(e)
        if state["service"] is None:
            raise HTTPException(503, detail=state["error"])
        return state["service"]

    @app.get("/health", response_model=Health, tags=["servis"])
    def health() -> Health:
        try:
            svc = get_service()
        except HTTPException as e:
            return Health(status="model yok", model_loaded=False, detail=e.detail)
        return Health(status="ok", model_loaded=True, model_created=svc.a.card["created"],
                      stations=len(svc.a.stations))

    @app.get("/stations", response_model=list[Station], tags=["istasyonlar"])
    def stations() -> list[dict]:
        return get_service().stations()

    @app.get("/forecast/{station}", response_model=Forecast, tags=["tahmin"],
             responses={404: {"description": "Bilinmeyen istasyon"},
                        503: {"description": "Güncel veri yok"}})
    def forecast(station: str) -> dict:
        svc = get_service()
        try:
            return svc.forecast(station)
        except KeyError:
            raise HTTPException(404, detail=f"Bilinmeyen istasyon: {station}. Geçerli "
                                            f"istasyonlar: {sorted(svc.a.stations)}") from None
        except DataUnavailable as e:
            raise HTTPException(503, detail=str(e)) from None

    @app.get("/alerts", response_model=list[Forecast | StationError], tags=["tahmin"])
    def alerts(only_alerts: bool = Query(False, description="Yalnızca uyarı ya da uyarı "
                                                           "riski olan istasyonlar")):
        return get_service().alerts(only_alerts=only_alerts)

    return app


app = create_app()
