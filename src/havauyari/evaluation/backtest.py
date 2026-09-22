"""Walk-forward (zamana göre ileri kayan) geri test.

- **Test pencereleri:** verinin son `n_folds × test_days` günü, ardışık ve çakışmasız.
  Varsayılan 12 × 30 gün ≈ son 1 yıl; böylece her mevsim, özellikle uyarıların yoğunlaştığı kış
  test edilir (Faz 1.3 notu: tek bir yaz penceresinde uyarı metrikleri anlamsız kalıyordu).
- **Genişleyen eğitim penceresi:** her fold'da test başlangıcından önceki tüm veri.
- **Arındırma (purge):** t satırının hedefi t+h'dir. Yalnızca t+h < test başlangıcı olan satırlar
  eğitime girer; aksi halde eğitim etiketleri test dönemindeki değerleri içerirdi.
- **Birleştirilmiş (pooled) metrikler:** tüm test tahminleri tek havuzda ölçülür. Uyarılar kış
  fold'larında yoğunlaştığı için fold ortalaması uyarı metriklerini çarpıtır.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from havauyari.alerts.aqi import ALERT_INDEX, UNHEALTHY_INDEX
from havauyari.evaluation.metrics import alert_metrics, regression_metrics
from havauyari.models.baselines import Predictor

SEASON_OF_MONTH = {12: "Kış", 1: "Kış", 2: "Kış", 3: "İlkbahar", 4: "İlkbahar", 5: "İlkbahar",
                   6: "Yaz", 7: "Yaz", 8: "Yaz", 9: "Sonbahar", 10: "Sonbahar", 11: "Sonbahar"}
SEASONS = ["Kış", "İlkbahar", "Yaz", "Sonbahar"]


@dataclass(frozen=True)
class Fold:
    number: int
    test_start: pd.Timestamp
    test_end: pd.Timestamp  # hariç


def make_folds(index: pd.DatetimeIndex, n_folds: int = 12, test_days: int = 30) -> list[Fold]:
    """Verinin sonuna dayanan, ardışık ve çakışmasız test pencereleri (eskiden yeniye)."""
    end = index.max() + pd.Timedelta(hours=1)
    length = pd.Timedelta(days=test_days)
    return [Fold(i, end - length * (n_folds - i), end - length * (n_folds - i - 1))
            for i in range(n_folds)]


def in_train_window(index: pd.DatetimeIndex, fold: Fold, horizon: int) -> np.ndarray:
    """Hedef anı (t+h) test başlangıcından önce olan satırlar."""
    return (index + pd.Timedelta(hours=horizon)) < fold.test_start


def in_test_window(index: pd.DatetimeIndex, fold: Fold) -> np.ndarray:
    return (index >= fold.test_start) & (index < fold.test_end)


def run_backtest(feats: pd.DataFrame, horizon: int, predictors: dict[str, Predictor],
                 folds: list[Fold], verbose: bool = False) -> pd.DataFrame:
    """Her fold ve model için test tahminlerini üretir. Dönüş: uzun biçimli tahmin tablosu."""
    target = f"target_h{horizon}"
    feats = feats.dropna(subset=[target])
    parts = []
    for fold in folds:
        train = feats[in_train_window(feats.index, fold, horizon)]
        test = feats[in_test_window(feats.index, fold)]
        if test.empty:
            continue
        for name, predict in predictors.items():
            pred = np.asarray(predict(train, test), dtype=float)
            parts.append(pd.DataFrame({
                "time": test.index,
                "target_time": test.index + pd.Timedelta(hours=horizon),
                "city": test["city"].to_numpy(),
                "fold": fold.number,
                "model": name,
                "y_true": test[target].to_numpy(),
                "y_pred": pred,
            }))
        if verbose:
            print(f"  fold {fold.number:2d}: {fold.test_start:%Y-%m-%d} → {fold.test_end:%Y-%m-%d}"
                  f"  eğitim={len(train):,}  test={len(test):,}")
    preds = pd.concat(parts, ignore_index=True)
    preds["season"] = preds["target_time"].dt.month.map(SEASON_OF_MONTH)
    return preds


def summarize(preds: pd.DataFrame, by: list[str] | None = None) -> pd.DataFrame:
    """Birleştirilmiş metrikler: model (ve `by` grupları) başına tek satır."""
    keys = ["model", *(by or [])]
    rows = []
    for key, g in preds.groupby(keys, observed=True, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        severe = alert_metrics(g["y_true"], g["y_pred"], UNHEALTHY_INDEX)
        rows.append({
            **dict(zip(keys, key, strict=True)),
            **regression_metrics(g["y_true"], g["y_pred"]),
            **alert_metrics(g["y_true"], g["y_pred"], ALERT_INDEX),
            "severe_recall": severe["alert_recall"],
            "severe_rate": severe["alert_rate"],
        })
    return pd.DataFrame(rows).set_index(keys)
