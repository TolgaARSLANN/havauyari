"""Walk-forward geri test: baseline'lar ve LightGBM.

Kullanım:
    python -m havauyari.models.train                      # 24 saat, 12 aylık fold, tüm modeller
    python -m havauyari.models.train --horizon 48 --folds 6
    python -m havauyari.models.train --baselines-only     # hızlı: yalnızca referans modeller

Çıktılar:
    reports/backtest_h{h}.md               sonuç raporu (repoya girer)
    data/processed/preds_h{h}.parquet      tüm test tahminleri (hata analizi için)
"""

from __future__ import annotations

import argparse
from datetime import date

import lightgbm as lgb
import numpy as np
import pandas as pd

from havauyari.alerts.aqi import ALERT_INDEX, UNHEALTHY_INDEX, threshold_concentration
from havauyari.config import PROCESSED_DIR, ROOT
from havauyari.data.clean import PROCESSED_PATH
from havauyari.evaluation.backtest import SEASONS, Fold, make_folds, run_backtest, summarize
from havauyari.evaluation.metrics import exceeds
from havauyari.features.build import build_all_cities, feature_columns
from havauyari.models.baselines import Predictor, baseline_predictors
from havauyari.reporting import to_markdown

REPORTS_DIR = ROOT / "reports"

LGBM_PARAMS = dict(n_estimators=500, learning_rate=0.05, num_leaves=63, subsample=0.8,
                   subsample_freq=1, colsample_bytree=0.8, random_state=0, verbose=-1)


def lightgbm_predictor(horizon: int, params: dict | None = None) -> Predictor:
    target = f"target_h{horizon}"

    def predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        cols = feature_columns(train)
        model = lgb.LGBMRegressor(**(params or LGBM_PARAMS))
        model.fit(train[cols], train[target])
        return model.predict(test[cols])

    return predict


def prepare_features(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    feats = build_all_cities(df, horizon)
    feats["city"] = feats["city"].astype("category")
    feats["city_code"] = feats["city"].cat.codes
    return feats


def build_report(preds: pd.DataFrame, folds: list[Fold], horizon: int) -> str:
    alert_c = threshold_concentration(ALERT_INDEX)
    severe_c = threshold_concentration(UNHEALTHY_INDEX)
    cols = ["mae", "rmse", "smape", "alert_recall", "alert_precision", "alert_f1", "severe_recall"]
    names = {"mae": "MAE", "rmse": "RMSE", "smape": "sMAPE %", "alert_recall": "uyarı recall",
             "alert_precision": "uyarı precision", "alert_f1": "uyarı F1",
             "severe_recall": f"recall ≥{severe_c}"}

    overall = summarize(preds)[cols].sort_values("mae").rename(columns=names)
    best_baseline = (summarize(preds[preds.model != "lightgbm"])["mae"].idxmin()
                     if "lightgbm" in preds.model.unique() else None)

    season = summarize(preds, ["season"])["mae"].unstack("season")
    season = season[[s for s in SEASONS if s in season.columns]]
    season_recall = summarize(preds, ["season"])["alert_recall"].unstack("season")
    season_recall = season_recall[season.columns]
    city = summarize(preds, ["city"])["mae"].unstack("city")
    city_recall = summarize(preds, ["city"])["alert_recall"].unstack("city")
    fold_mae = summarize(preds, ["fold"])["mae"].unstack("model")
    fold_mae.index = [f"{f.test_start:%Y-%m-%d}" for f in folds if f.number in fold_mae.index]
    fold_mae.index.name = "test başlangıcı"
    order = overall.index.tolist()
    for t in (season, season_recall, city, city_recall):
        t.index.name = "model"
    rate = preds.drop_duplicates(["time", "city"])
    alert_rate = exceeds(rate["y_true"], ALERT_INDEX).mean() * 100

    out = [
        f"# Geri Test Sonuçları: {horizon} saat sonrası PM2.5",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: "
        f"`python -m havauyari.models.train --horizon {horizon}`_",
        "",
        "## Kurulum",
        "",
        f"- **Test dönemi:** {folds[0].test_start:%Y-%m-%d} → {folds[-1].test_end:%Y-%m-%d}, "
        f"{len(folds)} ardışık {(folds[0].test_end - folds[0].test_start).days} günlük pencere",
        "- **Eğitim:** her pencerede, hedef anı test başlangıcından önce olan tüm satırlar "
        "(genişleyen pencere + arındırma)",
        f"- **Tahmin sayısı:** model başına {len(rate):,} (5 şehir); gerçek uyarı oranı "
        f"%{alert_rate:.1f}",
        f"- **Uyarı:** PM2.5 ≥ {alert_c} µg/m³ (hassas gruplar için sağlıksız); "
        f"ikinci kademe ≥ {severe_c} µg/m³",
        "- Metrikler tüm test tahminleri birleştirilerek hesaplanır (fold ortalaması değil).",
        "",
        "## Genel sonuç",
        "",
        to_markdown(overall, ".3f"),
        "",
    ]
    if best_baseline:
        lg, bb = overall.loc["lightgbm"], overall.loc[best_baseline]
        gain = (1 - lg["MAE"] / bb["MAE"]) * 100
        out += [f"LightGBM, en iyi referans modele ({best_baseline}) göre MAE'de **%{gain:.1f}** "
                f"{'iyi' if gain > 0 else 'kötü'}.", ""]
    out += [
        "## Mevsime göre", "", "### MAE", "", to_markdown(season.loc[order], ".2f"), "",
        "### Uyarı recall", "", to_markdown(season_recall.loc[order], ".3f"), "",
        "## Şehre göre", "", "### MAE", "", to_markdown(city.loc[order], ".2f"), "",
        "### Uyarı recall", "", to_markdown(city_recall.loc[order], ".3f"), "",
        "## Pencere bazında MAE", "", to_markdown(fold_mae[order], ".2f"), "",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--folds", type=int, default=12)
    parser.add_argument("--test-days", type=int, default=30)
    parser.add_argument("--baselines-only", action="store_true")
    args = parser.parse_args()

    df = pd.read_parquet(PROCESSED_PATH)
    feats = prepare_features(df, args.horizon)
    folds = make_folds(feats.index, args.folds, args.test_days)

    predictors = baseline_predictors(args.horizon)
    if not args.baselines_only:
        predictors["lightgbm"] = lightgbm_predictor(args.horizon)

    print(f"Geri test: {args.horizon} saat, {len(folds)} pencere, modeller: {list(predictors)}")
    preds = run_backtest(feats, args.horizon, predictors, folds, verbose=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(PROCESSED_DIR / f"preds_h{args.horizon}.parquet")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"backtest_h{args.horizon}.md"
    report_path.write_text(build_report(preds, folds, args.horizon) + "\n", encoding="utf-8")

    summary = summarize(preds)[["mae", "rmse", "alert_recall", "alert_f1"]].sort_values("mae")
    print(summary.round(3).to_string())
    print(f"[ok] {report_path}")


if __name__ == "__main__":
    main()
