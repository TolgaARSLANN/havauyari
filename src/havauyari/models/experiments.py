"""Zirve bastırma deneyleri (Faz 4.2): kayıp fonksiyonu, hedef dönüşümü, ağırlık, sınıflandırıcı.

Sorun (Faz 4.3): L2 kaybıyla eğitilen model gerçek ≥ 55,5 µg/m³ saatlerde ortalama −22,9 sapıyor;
nadir yüksek değerlerde "ortalamaya yakın" tahmin L2 için ucuz.

Adil kıyas protokolü (her aday için aynı):
- 24 aylık walk-forward geri test (istasyon hedefi, 24 s, gerçekçi özellik seti)
- Uyarı: her test penceresinin karar eşiği yalnızca önceki pencerelerden, recall ≥ %80 sağlayan en
  yüksek değer olarak seçilir (alerts.threshold). Değerlendirme son 12 pencere.
- ANA ÖLÇÜT: aynı recall hedefinde precision (daha az yanlış alarm). Yan ölçütler: MAE, RMSE,
  gerçek ≥ 55,5 saatlerde sapma, yeni başlayan uyarıların yakalanma oranı.

Kullanım:
    python -m havauyari.models.experiments                 # tüm adaylar (önbellekli)
    python -m havauyari.models.experiments --only tweedie   # tek aday
    -> reports/deney_zirve_h24.md, reports/deney_kaydi.csv
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from datetime import datetime

import lightgbm as lgb
import numpy as np
import pandas as pd

from havauyari.alerts.threshold import (
    CALIB_PREDS_PATH,
    GRID,
    PROBABILITY_GRID,
    apply_thresholds,
    binary_metrics,
    walk_forward_thresholds,
)
from havauyari.config import PROCESSED_DIR, ROOT
from havauyari.evaluation.metrics import exceeds, regression_metrics
from havauyari.features.build import feature_columns
from havauyari.models.baselines import Predictor
from havauyari.models.train import LGBM_PARAMS
from havauyari.reporting import to_markdown

HORIZON = 24
N_FOLDS = 24
EXP_DIR = PROCESSED_DIR / "experiments"
REPORT_PATH = ROOT / "reports" / "deney_zirve_h24.md"
LOG_PATH = ROOT / "reports" / "deney_kaydi.csv"
ALERT_LEVEL = 35.5


@dataclass
class Candidate:
    name: str
    description: str
    kind: str = "regressor"                 # "regressor" | "classifier"
    params: dict = field(default_factory=dict)
    transform: str | None = None            # None | "log1p"
    weight: str | None = None               # None | "linear"


CANDIDATES = [
    Candidate("l2", "Mevcut model: L2 kaybı, ham hedef (Faz 3.9)"),
    Candidate("log1p", "L2 kaybı, log(1+PM2.5) hedef", transform="log1p"),
    Candidate("tweedie", "Tweedie kaybı (varyans gücü 1,5)",
              params={"objective": "tweedie", "tweedie_variance_power": 1.5}),
    Candidate("agirlikli", "L2 kaybı, ağırlık = 1 + PM2.5 / 35,5", weight="linear"),
    Candidate("siniflandirici", "Doğrudan P(PM2.5 ≥ 35,5) tahmin eden ikili sınıflandırıcı",
              kind="classifier"),
]


def _sample_weight(y: pd.Series, how: str | None) -> np.ndarray | None:
    if how is None:
        return None
    if how == "linear":
        return (1.0 + y / ALERT_LEVEL).to_numpy()
    raise ValueError(how)


def make_predictor(c: Candidate, horizon: int = HORIZON) -> Predictor:
    target = f"target_h{horizon}"

    def predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        cols = feature_columns(train, realistic=True)
        y = train[target]
        params = {**LGBM_PARAMS, **c.params}
        if c.kind == "classifier":
            model = lgb.LGBMClassifier(**params)
            model.fit(train[cols], exceeds(y).astype(int))
            return model.predict_proba(test[cols])[:, 1]
        model = lgb.LGBMRegressor(**params)
        y_fit = np.log1p(y) if c.transform == "log1p" else y
        model.fit(train[cols], y_fit, sample_weight=_sample_weight(y, c.weight))
        pred = model.predict(test[cols])
        return np.expm1(pred) if c.transform == "log1p" else pred

    return predict


def run_candidate(c: Candidate, feats: pd.DataFrame, folds, force: bool = False) -> pd.DataFrame:
    """Adayın 24 pencerelik geri test tahminleri (önbellekli). 'l2' Faz 4.4 çıktısını kullanır."""
    from havauyari.evaluation.backtest import run_backtest

    EXP_DIR.mkdir(parents=True, exist_ok=True)
    path = EXP_DIR / f"{c.name}.parquet"
    if c.name == "l2" and CALIB_PREDS_PATH.exists() and not force:
        return pd.read_parquet(CALIB_PREDS_PATH).assign(model="l2")
    if path.exists() and not force:
        return pd.read_parquet(path)
    t0 = time.time()
    preds = run_backtest(feats, HORIZON, {c.name: make_predictor(c)}, folds, group_col="station")
    preds.to_parquet(path)
    print(f"  [{c.name}] {time.time() - t0:.0f} sn")
    return preds


# ---------------------------------------------------------------------------------------------
# Değerlendirme
# ---------------------------------------------------------------------------------------------
def evaluate(c: Candidate, preds: pd.DataFrame, now_values: pd.Series) -> dict:
    """Son 12 pencerede walk-forward uyarı metrikleri ve (regresörlerde) hata metrikleri."""
    folds = sorted(preds["fold"].unique())
    eval_folds = folds[len(folds) // 2:]
    grid = PROBABILITY_GRID if c.kind == "classifier" else GRID
    thresholds = walk_forward_thresholds(preds, eval_folds, grid=grid)
    q = apply_thresholds(preds, thresholds)
    alert = binary_metrics(q["gerçek"], q["uyarı"])

    # Yeni başlayan uyarılar: t anında istasyonda uyarı yok, t+24'te var
    key = pd.MultiIndex.from_frame(q[["time", "station"]])
    now = now_values.reindex(key).to_numpy()
    onset = q["gerçek"].to_numpy() & ~exceeds(now) & ~np.isnan(now)
    row = {
        "aday": c.name,
        "recall": alert["recall"],
        "precision": alert["precision"],
        "F1": alert["f1"],
        "yeni başlayan recall": q.loc[onset, "uyarı"].mean(),
        "eşik aralığı": f"{min(thresholds.values()):g}–{max(thresholds.values()):g}",
    }
    if c.kind == "regressor":
        last = preds[preds["fold"].isin(eval_folds)]
        reg = regression_metrics(last["y_true"], last["y_pred"])
        high = last[last["y_true"] >= 55.5]
        row.update({"MAE": reg["mae"], "RMSE": reg["rmse"],
                    "sapma ≥55,5": (high["y_pred"] - high["y_true"]).mean(),
                    "sapma <10": (last.loc[last["y_true"] < 10, "y_pred"]
                                  - last.loc[last["y_true"] < 10, "y_true"]).mean()})
    return row


def build_report(results: pd.DataFrame) -> str:
    view = results.set_index("aday")
    desc = pd.Series({c.name: c.description for c in CANDIDATES}, name="açıklama")
    desc.index.name = "aday"
    best = view["precision"].idxmax()
    base = view.loc["l2"]
    return "\n".join([
        "# Deney: Zirve Bastırma, 24 Saat (İstasyon Hedefi)",
        "",
        f"_Oluşturulma: {datetime.now():%Y-%m-%d} · Üreten: "
        "`python -m havauyari.models.experiments`_",
        "",
        "## Adaylar",
        "",
        to_markdown(desc),
        "",
        "## Protokol",
        "",
        "24 aylık walk-forward geri test; son 12 pencere değerlendirilir. Her pencerenin uyarı "
        "karar eşiği yalnızca önceki pencerelerin tahminlerinden, recall ≥ %80 sağlayan en yüksek "
        "değer olarak seçilir. Ana ölçüt: bu recall düzeyinde **precision**.",
        "",
        "## Sonuçlar",
        "",
        to_markdown(view, ".3f"),
        "",
        f"En yüksek precision: **{best}** ({view.loc[best, 'precision']:.3f}; mevcut model "
        f"{base['precision']:.3f}).",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="Yalnızca bu adaylar")
    parser.add_argument("--force", action="store_true", help="Önbelleği yok say")
    args = parser.parse_args()

    from havauyari.evaluation.backtest import make_folds
    from havauyari.models.train_station import prepare

    feats = prepare()
    folds = make_folds(feats.index, N_FOLDS)
    now_values = feats.reset_index().set_index(["time", "station"])["station_pm25"]
    now_values = now_values[~now_values.index.duplicated()]

    candidates = [c for c in CANDIDATES if not args.only or c.name in args.only]
    rows = []
    for c in candidates:
        print(f"Aday: {c.name} — {c.description}")
        preds = run_candidate(c, feats, folds, force=args.force)
        rows.append(evaluate(c, preds, now_values))
    results = pd.DataFrame(rows)
    print(results.round(3).to_string(index=False))

    stamp = datetime.now().isoformat(timespec="seconds")
    log = results.assign(zaman=stamp, deney="zirve_bastirma_h24")
    log.to_csv(LOG_PATH, mode="a", header=not LOG_PATH.exists(), index=False)
    if not args.only:
        REPORT_PATH.write_text(build_report(results) + "\n", encoding="utf-8")
        print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
