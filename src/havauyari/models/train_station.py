"""İstasyon hedefli geri test (Faz 3.9): gerçek SİM ölçümünü 24 saat önceden tahmin etmek.

Kullanım:
    python -m havauyari.models.train_station            # 12 aylık walk-forward, tüm modeller

Modeller:
    Referanslar : persistence, hareketli ortalama, klimatoloji, 1 hafta önce,
                  ham CAMS (İYİMSER), istasyon ortalamasına ölçeklenmiş CAMS (İYİMSER)
    lgbm_gercekci: CAMS yalnızca t anına kadar + geçmişte yayımlanmış hava tahminleri
                   -> bugün birebir uygulanabilir, ALT SINIR
    lgbm_iyimser : + CAMS'ın hedef anı ve öncesindeki değerleri (analiz, gerçek tahmin değil)
                   -> ham CAMS referansıyla aynı avantaj, ÜST SINIR

Çıktılar:
    reports/backtest_istasyon_h24.md
    data/processed/preds_station_h24.parquet
"""

from __future__ import annotations

import argparse
from datetime import date

import pandas as pd

from havauyari.alerts.aqi import ALERT_INDEX, threshold_concentration
from havauyari.config import PROCESSED_DIR, ROOT
from havauyari.data.stations import STATIONS_PATH
from havauyari.evaluation.backtest import (
    SEASONS,
    Fold,
    align_models,
    make_folds,
    run_backtest,
    summarize,
)
from havauyari.evaluation.metrics import exceeds
from havauyari.features.build import STATION_TARGET, build_all_stations, feature_columns
from havauyari.models.baselines import baseline_predictors
from havauyari.models.train import lightgbm_predictor
from havauyari.reporting import to_markdown

HORIZON = 24
REPORT_PATH = ROOT / "reports" / f"backtest_istasyon_h{HORIZON}.md"
PREDS_PATH = PROCESSED_DIR / f"preds_station_h{HORIZON}.parquet"
LOW_CONFIDENCE = {"ankara_kecioren_sanatoryum", "ankara_etimesgut"}
REALISTIC, OPTIMISTIC = "lgbm_gercekci", "lgbm_iyimser"

COLS = {"mae": "MAE", "rmse": "RMSE", "alert_recall": "uyarı recall",
        "alert_precision": "uyarı precision", "alert_f1": "uyarı F1",
        "severe_recall": "recall ≥55,5"}


def prepare(horizon: int = HORIZON) -> pd.DataFrame:
    data = pd.read_parquet(STATIONS_PATH)
    feats = build_all_stations(data, horizon)
    feats["station_code"] = feats["station"].cat.codes
    feats["city_code"] = feats["city"].cat.codes
    return feats


def predictors(horizon: int = HORIZON) -> dict:
    preds = baseline_predictors(horizon, col=STATION_TARGET, group="station", with_cams=True)
    preds[REALISTIC] = lightgbm_predictor(horizon, realistic=True)
    preds[OPTIMISTIC] = lightgbm_predictor(horizon, realistic=False)
    return preds


def _table(preds: pd.DataFrame, by: str, metric: str, order: list[str]) -> pd.DataFrame:
    t = summarize(preds, [by])[metric].unstack(by).loc[order]
    t.index.name = "model"
    return t


def build_report(preds: pd.DataFrame, folds: list[Fold], n_features: tuple[int, int]) -> str:
    alert_c = threshold_concentration(ALERT_INDEX)
    overall = summarize(preds)[list(COLS)].sort_values("mae").rename(columns=COLS)
    order = overall.index.tolist()
    trusted = preds[~preds["station"].isin(LOW_CONFIDENCE)]
    overall_trusted = summarize(trusted)[list(COLS)].loc[order].rename(columns=COLS)

    by_station_mae = _table(preds, "station", "mae", order)
    by_station_rec = _table(preds, "station", "alert_recall", order)
    by_season_mae = _table(preds, "season", "mae", order)[
        [s for s in SEASONS if s in preds["season"].unique()]]
    by_season_rec = _table(preds, "season", "alert_recall", order)[by_season_mae.columns]

    one = preds.drop_duplicates(["time", "station"])
    rate = exceeds(one["y_true"]).mean() * 100

    def gain(a: str, b: str, frame: pd.DataFrame = overall) -> str:
        return f"%{(1 - frame.loc[a, 'MAE'] / frame.loc[b, 'MAE']) * 100:.1f}"

    references = [m for m in order if not m.startswith("lgbm")]
    best_ref = min(references, key=lambda m: overall.loc[m, "MAE"])
    lines = [
        f"# Geri Test: İstasyon Ölçümü, {HORIZON} Saat Sonrası PM2.5",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: "
        "`python -m havauyari.models.train_station`_",
        "",
        "## Kurulum",
        "",
        "- **Hedef:** Çevre Bakanlığı SİM istasyonunda **gerçekten ölçülen** saatlik PM2.5 "
        "(8 kentsel istasyon, 5 şehir). Ölçülmemiş saatler hedef olarak kullanılmaz.",
        f"- **Test:** {folds[0].test_start:%Y-%m-%d} → {folds[-1].test_end:%Y-%m-%d}, "
        f"{len(folds)} × 30 gün walk-forward, genişleyen eğitim + arındırma.",
        f"- **Karşılaştırma:** tüm modeller aynı {len(one):,} (zaman, istasyon) satırında "
        f"ölçülür. Gerçek uyarı oranı (PM2.5 ≥ {alert_c}): %{rate:.1f}.",
        f"- **lgbm_gercekci** ({n_features[0]} özellik): istasyon geçmişi, CAMS'ın t anına kadarki "
        "değerleri, ERA5 gözlemleri ve *o gün yayımlanmış* 1 günlük hava tahminleri. Bugün "
        "birebir uygulanabilir → **alt sınır**.",
        f"- **lgbm_iyimser** ({n_features[1]} özellik): + CAMS'ın hedef anı ve öncesindeki "
        "değerleri. Geçmiş CAMS tahmin arşivi olmadığından CAMS analizi kullanılır; `cams_raw` ve "
        "`cams_scaled` referanslarıyla aynı avantaja sahiptir → **üst sınır**.",
        "",
        "## Genel sonuç",
        "",
        to_markdown(overall, ".3f"),
        "",
        f"- Gerçekçi model, en iyi referansa ({best_ref}) göre MAE'de "
        f"**{gain(REALISTIC, best_ref)}**, ham CAMS'a göre **{gain(REALISTIC, 'cams_raw')}** iyi.",
        f"- İyimser model, ham CAMS'a göre **{gain(OPTIMISTIC, 'cams_raw')}**, ölçeklenmiş CAMS'a "
        f"göre **{gain(OPTIMISTIC, 'cams_scaled')}** iyi.",
        "",
        "### Ankara hariç (düşük güvenli 2 istasyon çıkarıldığında)",
        "",
        to_markdown(overall_trusted, ".3f"),
        "",
        "## İstasyona göre",
        "",
        "Ankara istasyonları düşük güvenlidir (kış gecesi değerleri şüpheli düşük; bkz. "
        "reports/istasyon_veri_kalitesi.md).",
        "",
        "### MAE", "", to_markdown(by_station_mae, ".2f"), "",
        "### Uyarı recall", "", to_markdown(by_station_rec, ".3f"), "",
        "## Mevsime göre", "",
        "### MAE", "", to_markdown(by_season_mae, ".2f"), "",
        "### Uyarı recall", "", to_markdown(by_season_rec, ".3f"), "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folds", type=int, default=12)
    args = parser.parse_args()

    feats = prepare()
    folds = make_folds(feats.index, args.folds)
    n_feat = (len(feature_columns(feats, realistic=True)), len(feature_columns(feats)))
    print(f"Özellik sayısı: gerçekçi={n_feat[0]}, iyimser={n_feat[1]}")
    raw = run_backtest(feats, HORIZON, predictors(), folds, verbose=True, group_col="station")
    preds = align_models(raw, group_col="station")
    print(f"Hizalama: {len(raw):,} -> {len(preds):,} satır")

    PREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    preds.to_parquet(PREDS_PATH)
    REPORT_PATH.write_text(build_report(preds, folds, n_feat) + "\n", encoding="utf-8")
    summary = summarize(preds)[["mae", "rmse", "alert_recall", "alert_precision", "alert_f1"]]
    print(summary.sort_values("mae").round(3).to_string())
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
