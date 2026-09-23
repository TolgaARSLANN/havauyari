"""Uyarı karar eşiği (Faz 4.4): test dönemini görmeden, geçmiş tahminlerden seçilir.

Sorun: model zirveleri bastırdığı için "tahmin ≥ 35,5 ise uyar" kuralı gerçek uyarıların ~%34'ünü
kaçırıyor (Faz 4.3). Çözüm: resmî eşik (35,5) GERÇEK değeri sınıflandırmak için aynen kalır; modelin
TAHMİNİNE uygulanan karar eşiği ise daha düşük olabilir.

Hedef (ürün kararı): gerçek uyarıların en az %80'ini yakalamak. Seçim kuralı: geçmiş tahminlerde
recall ≥ hedef sağlayan EN YÜKSEK eşik (yanlış alarmı en aza indirmek için), üst sınır 35,5.

Walk-forward seçim: her test penceresi için eşik yalnızca o pencereden ÖNCEKİ pencerelerin
tahminlerinden seçilir.

Kullanım:
    python -m havauyari.alerts.threshold
    -> reports/uyari_esigi_h24.md, models/alert_threshold.json
"""

from __future__ import annotations

import argparse
import json
from datetime import date

import numpy as np
import pandas as pd

from havauyari.alerts.aqi import ALERT_INDEX, threshold_concentration
from havauyari.config import MODELS_DIR, PROCESSED_DIR, ROOT
from havauyari.evaluation.metrics import exceeds
from havauyari.reporting import to_markdown

TARGET_RECALL = 0.80
OFFICIAL = threshold_concentration(ALERT_INDEX)            # 35,5
GRID = np.round(np.arange(15.0, OFFICIAL + 0.001, 0.5), 1)  # 15,0 … 35,5
MODEL = "lgbm_gercekci"

CALIB_PREDS_PATH = PROCESSED_DIR / "preds_station_h24_24fold.parquet"
REPORT_PATH = ROOT / "reports" / "uyari_esigi_h24.md"
THRESHOLD_PATH = MODELS_DIR / "alert_threshold.json"


def binary_metrics(truth: np.ndarray, alert: np.ndarray) -> dict[str, float]:
    truth, alert = np.asarray(truth, bool), np.asarray(alert, bool)
    tp = int((truth & alert).sum())
    recall = tp / truth.sum() if truth.sum() else 0.0
    precision = tp / alert.sum() if alert.sum() else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return {"recall": recall, "precision": precision, "f1": f1,
            "uyarı_saati": int(alert.sum()), "gerçek_uyarı": int(truth.sum())}


def threshold_for_recall(y_true, y_pred, target: float = TARGET_RECALL,
                         grid: np.ndarray = GRID) -> float:
    """recall(y_pred ≥ eşik) ≥ hedef sağlayan en yüksek eşik; hiçbiri sağlamazsa en düşük eşik."""
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    ok = ~(np.isnan(y_true) | np.isnan(y_pred))
    truth, pred = exceeds(y_true[ok]), y_pred[ok]
    if truth.sum() == 0:
        return float(grid.max())
    best = float(grid.min())
    for thr in grid:  # artan sırada: recall azalır
        if (truth & (pred >= thr)).sum() / truth.sum() >= target:
            best = float(thr)
    return best


def walk_forward_thresholds(preds: pd.DataFrame, eval_folds: list[int],
                            target: float = TARGET_RECALL) -> dict[int, float]:
    """Her değerlendirme penceresi için eşik: yalnızca daha önceki pencerelerin tahminleri."""
    out = {}
    for k in eval_folds:
        past = preds[preds["fold"] < k]
        if past.empty:
            raise ValueError(f"Pencere {k} için geçmiş tahmin yok")
        out[k] = threshold_for_recall(past["y_true"], past["y_pred"], target)
    return out


def apply_thresholds(preds: pd.DataFrame, thresholds: dict[int, float]) -> pd.DataFrame:
    q = preds[preds["fold"].isin(thresholds)].copy()
    q["eşik"] = q["fold"].map(thresholds)
    q["uyarı"] = q["y_pred"] >= q["eşik"]
    q["gerçek"] = exceeds(q["y_true"])
    return q


# ---------------------------------------------------------------------------------------------
def run_calibration_backtest(n_folds: int = 24) -> pd.DataFrame:
    """Ana model için 24 pencerelik geri test (ilk 12 pencere yalnızca eşik ayarı içindir)."""
    from havauyari.evaluation.backtest import make_folds, run_backtest
    from havauyari.models.train import lightgbm_predictor
    from havauyari.models.train_station import HORIZON, prepare

    feats = prepare()
    folds = make_folds(feats.index, n_folds)
    preds = run_backtest(feats, HORIZON, {MODEL: lightgbm_predictor(HORIZON, realistic=True)},
                         folds, verbose=True, group_col="station")
    preds.to_parquet(CALIB_PREDS_PATH)
    return preds


def build_report(preds: pd.DataFrame, thresholds: dict[int, float], final: float,
                 n_eval: int) -> str:
    q = apply_thresholds(preds, thresholds)
    fixed = binary_metrics(q["gerçek"], q["y_pred"] >= OFFICIAL)
    tuned = binary_metrics(q["gerçek"], q["uyarı"])
    weeks = (q["time"].max() - q["time"].min()).days / 7
    n_st = q["station"].nunique()
    summary = pd.DataFrame({f"sabit {OFFICIAL}": fixed, "walk-forward eşik": tuned}).T
    summary["uyarı saati / istasyon-hafta"] = summary["uyarı_saati"] / (weeks * n_st)
    summary.index.name = "karar kuralı"

    summary = summary.astype({"uyarı_saati": int, "gerçek_uyarı": int})

    per_fold = pd.DataFrame([
        {"test başlangıcı": g["time"].min().strftime("%Y-%m-%d"),
         "eşik": float(g["eşik"].iloc[0]), **binary_metrics(g["gerçek"], g["uyarı"])}
        for _, g in q.groupby("fold")]).set_index("test başlangıcı")

    per_station = {}
    for st, g in q.groupby("station", observed=True):
        tuned_st = binary_metrics(g["gerçek"], g["uyarı"])
        per_station[st] = {
            "gerçek uyarı": int(g["gerçek"].sum()),
            f"recall (sabit {OFFICIAL})": binary_metrics(g["gerçek"],
                                                         g["y_pred"] >= OFFICIAL)["recall"],
            "recall (walk-forward)": tuned_st["recall"],
            "precision (walk-forward)": tuned_st["precision"]}
    per_station = pd.DataFrame(per_station).T
    per_station["gerçek uyarı"] = per_station["gerçek uyarı"].astype(int)
    per_station.index.name = "istasyon"

    return "\n".join([
        "# Uyarı Karar Eşiği: İstasyon Hedefi, 24 Saat",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: "
        f"`python -m havauyari.alerts.threshold` · Model: `{MODEL}`_",
        "",
        "## Yöntem",
        "",
        f"- Gerçek uyarı = ölçülen PM2.5 ≥ {OFFICIAL} µg/m³ (resmî eşik, değişmez).",
        "- Karar kuralı: model tahmini ≥ karar eşiği ise uyar. "
        f"Hedef: recall ≥ %{TARGET_RECALL * 100:.0f}.",
        "- Eşik seçimi: recall hedefini sağlayan **en yüksek** eşik (yanlış alarmı en aza "
        f"indirir), aralık {GRID.min()}–{GRID.max()}.",
        f"- **Walk-forward:** 24 aylık geri testin son {n_eval} penceresi değerlendirilir; her "
        "pencerenin eşiği yalnızca kendisinden önceki pencerelerin tahminlerinden seçilir. İlk "
        "pencereler daha az veriyle eğitilmiş modellerden geldiği için seçilen eşikler hafif "
        "temkinlidir.",
        "",
        "## Sonuç (son 12 ay)",
        "",
        to_markdown(summary.drop(columns=["uyarı_saati"]), ".3f"),
        "",
        "## Pencere bazında",
        "",
        to_markdown(per_fold, ".3f"),
        "",
        "## İstasyon bazında",
        "",
        to_markdown(per_station, ".3f"),
        "",
        "## Canlı sistem eşiği",
        "",
        f"Tüm {preds['fold'].nunique()} pencerenin tahminlerinden seçilen eşik: **{final} µg/m³** "
        f"(`{THRESHOLD_PATH.relative_to(ROOT).as_posix()}`).",
        "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true", help="Kayıtlı 24 pencere tahminini kullan")
    args = parser.parse_args()

    preds = (pd.read_parquet(CALIB_PREDS_PATH) if args.reuse and CALIB_PREDS_PATH.exists()
             else run_calibration_backtest())
    folds = sorted(preds["fold"].unique())
    eval_folds = folds[len(folds) // 2:]
    thresholds = {int(k): v for k, v in walk_forward_thresholds(preds, eval_folds).items()}
    final = threshold_for_recall(preds["y_true"], preds["y_pred"])

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    THRESHOLD_PATH.write_text(json.dumps({
        "model": MODEL, "horizon_h": 24, "decision_threshold_ugm3": final,
        "official_threshold_ugm3": OFFICIAL, "target_recall": TARGET_RECALL,
        "calibrated_on": f"{preds['time'].min():%Y-%m-%d} → {preds['time'].max():%Y-%m-%d}",
        "created": date.today().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(preds, thresholds, final, len(eval_folds)) + "\n",
                           encoding="utf-8")
    print("walk-forward eşikler:", thresholds)
    print(f"canlı eşik: {final}")
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
