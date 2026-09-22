"""Walk-forward doğrulama ile baseline'ları ve LightGBM'i karşılaştırır.

Kullanım:
    python -m havauyari.models.train --horizon 24 --folds 4
"""

from __future__ import annotations

import argparse

import lightgbm as lgb
import pandas as pd

from havauyari.config import PROCESSED_DIR, TARGET
from havauyari.evaluation.metrics import alert_metrics, regression_metrics
from havauyari.features.build import build_all_cities, feature_columns
from havauyari.models.baselines import moving_average, persistence, seasonal_naive


def walk_forward_splits(index: pd.DatetimeIndex, n_folds: int, test_days: int = 30):
    """Zamana göre ileri kayan train/test pencereleri. Test hep train'in sonrasındadır."""
    end = index.max()
    for k in range(n_folds, 0, -1):
        test_start = end - pd.Timedelta(days=test_days * k)
        test_end = test_start + pd.Timedelta(days=test_days)
        yield index < test_start, (index >= test_start) & (index < test_end)


def evaluate(df: pd.DataFrame, horizon: int, n_folds: int) -> pd.DataFrame:
    target = f"target_h{horizon}"
    feats = build_all_cities(df, horizon).dropna(subset=[target])
    feats["city_code"] = feats["city"].astype("category").cat.codes
    x_cols = feature_columns(feats)

    preds = {
        "persistence": pd.concat(persistence(g[TARGET], horizon) for _, g in feats.groupby("city")),
        "seasonal_naive": pd.concat(
            seasonal_naive(g[TARGET], horizon, season=168) for _, g in feats.groupby("city")
        ),
        "moving_avg_24": pd.concat(
            moving_average(g[TARGET], horizon) for _, g in feats.groupby("city")
        ),
    }
    rows = []
    for fold, (tr, te) in enumerate(walk_forward_splits(feats.index, n_folds)):
        test = feats[te]
        for name, p in preds.items():
            p = p[te].to_numpy()
            rows.append({"fold": fold, "model": name,
                         **regression_metrics(test[target], p), **alert_metrics(test[target], p)})

        model = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, num_leaves=63,
                                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                  verbose=-1)
        model.fit(feats.loc[tr, x_cols], feats.loc[tr, target])
        p = model.predict(test[x_cols])
        rows.append({"fold": fold, "model": "lightgbm",
                     **regression_metrics(test[target], p), **alert_metrics(test[target], p)})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--folds", type=int, default=4)
    args = parser.parse_args()

    df = pd.read_parquet(PROCESSED_DIR / "all_cities.parquet")
    res = evaluate(df, args.horizon, args.folds)
    summary = res.groupby("model")[["mae", "rmse", "smape", "alert_recall", "alert_f1"]].mean()
    print(summary.sort_values("mae").round(3).to_string())


if __name__ == "__main__":
    main()
