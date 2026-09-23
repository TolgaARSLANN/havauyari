"""Tahmin akışı (Faz 5.1): canlı veri -> eğitimdeki aynı temizlik/özellikler -> tahmin.

Bir istasyon için çıktı: 24 saat sonrası PM2.5 tahmini, %80'lik aralık, AQI kategorisi, istasyon
eşiğine göre uyarı kararı, "uyarı riski" bayrağı ve tahminin açıklaması (özellik katkıları).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import lightgbm as lgb
import pandas as pd

from havauyari.alerts.aqi import aqi_category, pm25_to_aqi
from havauyari.alerts.threshold import decision_threshold
from havauyari.config import MODELS_DIR, TIMEZONE
from havauyari.data.clean import clean as clean_openmeteo
from havauyari.data.stations import clean_station
from havauyari.features.build import FEATURE_FFILL_HOURS, STATION_TARGET, build_station_features
from havauyari.models.final import explain_row, family_of
from havauyari.models.intervals import apply_intervals
from havauyari.serving.data import DataProvider

HORIZON = 24
OFFICIAL_ALERT = 35.5
STATION_COLS = ["station_pm25", "station_pm10"]


class DataUnavailable(RuntimeError):
    """Tahmin için gerekli güncel veri yok (örn. istasyon son saatlerde ölçüm yapmamış)."""


@dataclass
class Artifacts:
    booster: lgb.Booster
    card: dict
    thresholds: dict
    interval_table: pd.DataFrame
    stations: dict[str, dict]


def load_artifacts(models_dir: Path = MODELS_DIR) -> Artifacts:
    card = json.loads((models_dir / "model_card.json").read_text(encoding="utf-8"))
    model_path = models_dir / Path(card["model_file"]).name
    if not model_path.exists():
        raise FileNotFoundError(f"Model dosyası yok: {model_path}. "
                                "`python -m havauyari.models.final` ile üretin.")
    interval = json.loads((models_dir / "prediction_interval.json").read_text(encoding="utf-8"))
    table = pd.DataFrame({"q_low": interval["q_low"], "q_high": interval["q_high"]},
                         index=pd.CategoricalIndex(interval["bin_labels"],
                                                   categories=interval["bin_labels"]))
    registry = json.loads((models_dir / "stations.json").read_text(encoding="utf-8"))
    return Artifacts(
        booster=lgb.Booster(model_file=str(model_path)),
        card=card,
        thresholds=json.loads((models_dir / "alert_threshold.json").read_text(encoding="utf-8")),
        interval_table=table,
        stations={s["slug"]: s for s in registry},
    )


def local_now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None, minute=0, second=0,
                                                     microsecond=0)


def prepare_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Eğitimdeki temizlik: CAMS/meteoroloji fiziksel sınırlar + kısa boşluk, istasyon kuralları."""
    om_cols = [c for c in raw.columns if c not in ("station", STATION_TARGET, "station_pm10")
               and not c.startswith("fc_")]
    om, _ = clean_openmeteo(raw[om_cols])
    st, _ = clean_station(raw[STATION_COLS].rename(columns={"station_pm25": "PM25",
                                                            "station_pm10": "PM10"}))
    st = st.rename(columns={"PM25": "station_pm25", "PM10": "station_pm10"})
    fc = raw[[c for c in raw.columns if c.startswith("fc_")]]
    df = om.join(st).join(fc)
    df.insert(0, "station", raw["station"].iloc[0])
    return df


class ForecastService:
    def __init__(self, artifacts: Artifacts, provider: DataProvider,
                 clock: Callable[[], datetime] = local_now):
        self.a = artifacts
        self.provider = provider
        self.clock = clock
        self._cache: dict[tuple[str, datetime], dict] = {}

    # --- istasyonlar ---------------------------------------------------------------------
    def stations(self) -> list[dict]:
        return [{**s, "decision_threshold": decision_threshold(slug, self.a.thresholds)}
                for slug, s in self.a.stations.items()]

    # --- tahmin --------------------------------------------------------------------------
    def forecast(self, slug: str) -> dict:
        if slug not in self.a.stations:
            raise KeyError(slug)
        now = self.clock()
        key = (slug, now)
        if key in self._cache:                      # Faz 5.4: aynı saat içinde tekrar çekme
            return self._cache[key]
        result = self._forecast(self.a.stations[slug], now)
        self._cache = {k: v for k, v in self._cache.items() if k[1] == now}  # eski saatleri at
        self._cache[key] = result
        return result

    def _features(self, station: dict, feats: pd.DataFrame) -> pd.DataFrame:
        out = feats.copy()
        out["station_code"] = self.a.card["station_codes"][station["slug"]]
        out["city_code"] = self.a.card["city_codes"][station["city"]]
        return out[self.a.card["features"]]

    def _forecast(self, station: dict, now: datetime) -> dict:
        raw = self.provider.station_frame(station, now)
        frame = prepare_frame(raw)
        feats = build_station_features(frame, HORIZON)
        if now not in feats.index or pd.isna(feats.at[now, STATION_TARGET]):
            raise DataUnavailable(
                f"{station['name']}: son {FEATURE_FFILL_HOURS} saatte PM2.5 ölçümü yapılmamış; "
                "bu istasyon için şu anda tahmin üretilemiyor.")

        X = self._features(station, feats.loc[[now]])
        pred = max(float(self.a.booster.predict(X)[0]), 0.0)
        trajectory = self._trajectory(station, raw, feats, now)
        lo, hi = apply_intervals([pred], self.a.interval_table)
        threshold = decision_threshold(station["slug"], self.a.thresholds)
        expl = explain_row(self.a.booster, X, top=5)

        measured = raw[STATION_TARGET].loc[:now].dropna()
        return {
            "station": station["slug"],
            "station_name": station["name"],
            "city": station["city"],
            "issued_at": now,
            "target_time": now + timedelta(hours=HORIZON),
            "pm25": round(pred, 1),
            "interval_80": {"low": round(float(lo[0]), 1), "high": round(float(hi[0]), 1)},
            "aqi": pm25_to_aqi(pred),
            "category": aqi_category(pred),
            "alert": {
                "is_alert": bool(pred >= threshold),
                "decision_threshold": threshold,
                "official_threshold": OFFICIAL_ALERT,
                "risk": bool(hi[0] >= OFFICIAL_ALERT),
            },
            "explanation": {
                "base_value": round(float(expl.loc["taban (ortalama)", "katkı (µg/m³)"]), 2),
                "top_features": [
                    {"feature": f, "family": family_of(f),
                     "value": None if pd.isna(v) else round(float(v), 3),
                     "contribution": round(float(c), 2)}
                    for f, (v, c) in expl.drop(index=["taban (ortalama)", "diğer özellikler"])
                    .iterrows()],
                "other_features": round(float(expl.loc["diğer özellikler", "katkı (µg/m³)"]), 2),
            },
            "latest_measurement": {
                "time": measured.index[-1] if len(measured) else None,
                "pm25": None if measured.empty else round(float(measured.iloc[-1]), 1),
            },
            "model": {"name": self.a.card["model"], "created": self.a.card["created"],
                      "trained_on": self.a.card["trained_on"]},
            "trajectory": trajectory,
            "history": measurement_history(raw, now),
        }

    def _trajectory(self, station: dict, raw: pd.DataFrame, feats: pd.DataFrame,
                    now: datetime, hours_back: int = 72) -> list[dict]:
        """Son `hours_back + 24` saatte her saat verilmiş 24 saatlik tahminler.

        t anında verilen tahmin t+24'ü hedefler. Son 24 saatte verilenler önümüzdeki 24 saati
        kapsar (ileriye dönük eğri); daha öncekiler, gerçekleşen ölçümle karşılaştırılabilir
        (canlı performans). Her tahmin yalnızca kendi t anına kadarki veriyi kullanır.
        """
        start = now - timedelta(hours=hours_back + HORIZON - 1)
        issued = feats.loc[start:now]
        issued = issued[issued[STATION_TARGET].notna()]
        if issued.empty:
            return []
        pred = self.a.booster.predict(self._features(station, issued)).clip(min=0)
        lo, hi = apply_intervals(pred, self.a.interval_table)
        target = issued.index + timedelta(hours=HORIZON)
        actual = raw[STATION_TARGET].reindex(target).to_numpy()
        return [{"issued_at": i, "target_time": t, "pm25": round(float(p), 1),
                 "low": round(float(a), 1), "high": round(float(b), 1),
                 "actual": None if pd.isna(y) else round(float(y), 1)}
                for i, t, p, a, b, y in zip(issued.index, target, pred, lo, hi, actual,
                                            strict=True)]

    def alerts(self, only_alerts: bool = False) -> list[dict]:
        out = []
        for slug in self.a.stations:
            try:
                f = self.forecast(slug)
            except DataUnavailable as e:
                out.append({"station": slug, "error": str(e)})
                continue
            if not only_alerts or f["alert"]["is_alert"] or f["alert"]["risk"]:
                out.append(f)
        return out


def measurement_history(raw: pd.DataFrame, now: datetime, hours: int = 72) -> list[dict]:
    """Son `hours` saatin istasyon ölçümleri (grafik için)."""
    s = raw[STATION_TARGET].loc[now - timedelta(hours=hours - 1):now]
    return [{"time": t, "pm25": None if pd.isna(v) else round(float(v), 1)}
            for t, v in s.items()]
