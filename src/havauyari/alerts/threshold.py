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
                            target: float = TARGET_RECALL,
                            grid: np.ndarray = GRID) -> dict[int, float]:
    """Her değerlendirme penceresi için eşik: yalnızca daha önceki pencerelerin tahminleri.

    `grid`, tahminin ölçeğine uygun olmalıdır: konsantrasyon (µg/m³) için GRID, olasılık
    üreten bir sınıflandırıcı için PROBABILITY_GRID.
    """
    out = {}
    for k in eval_folds:
        past = preds[preds["fold"] < k]
        if past.empty:
            raise ValueError(f"Pencere {k} için geçmiş tahmin yok")
        out[k] = threshold_for_recall(past["y_true"], past["y_pred"], target, grid)
    return out


PROBABILITY_GRID = np.round(np.arange(0.01, 1.0, 0.01), 2)
MIN_GROUP_ALERTS = 50


def walk_forward_group_thresholds(preds: pd.DataFrame, eval_folds: list[int], group_col: str,
                                  target: float = TARGET_RECALL, grid: np.ndarray = GRID,
                                  min_alerts: int = MIN_GROUP_ALERTS) -> pd.Series:
    """Grup (istasyon / mevsim) başına walk-forward eşik; satır bazında eşik serisi döner.

    Her pencere k ve grup g için eşik yalnızca k'dan önceki pencerelerde g'ye ait tahminlerden
    seçilir. Geçmişte g için `min_alerts`'ten az gerçek uyarı varsa genel eşik kullanılır.
    """
    out = pd.Series(np.nan, index=preds.index)
    for k in eval_folds:
        past = preds[preds["fold"] < k]
        if past.empty:
            raise ValueError(f"Pencere {k} için geçmiş tahmin yok")
        fallback = threshold_for_recall(past["y_true"], past["y_pred"], target, grid)
        current = preds["fold"] == k
        for g in preds.loc[current, group_col].unique():
            pg = past[past[group_col] == g]
            thr = (threshold_for_recall(pg["y_true"], pg["y_pred"], target, grid)
                   if exceeds(pg["y_true"]).sum() >= min_alerts else fallback)
            out[current & (preds[group_col] == g)] = thr
    return out


def compare_strategies(preds: pd.DataFrame, eval_folds: list[int]) -> pd.DataFrame:
    """Tek eşik / mevsime göre / istasyona göre eşik stratejilerini son pencerelerde kıyaslar."""
    from havauyari.evaluation.backtest import SEASON_OF_MONTH

    p = preds.assign(season=preds["target_time"].dt.month.map(SEASON_OF_MONTH))
    last = p["fold"].isin(eval_folds)
    truth = exceeds(p.loc[last, "y_true"])
    glob = p["fold"].map(walk_forward_thresholds(p, eval_folds))
    strategies = {
        "tek eşik": glob,
        "mevsime göre": walk_forward_group_thresholds(p, eval_folds, "season"),
        "istasyona göre": walk_forward_group_thresholds(p, eval_folds, "station"),
    }
    weeks = (p.loc[last, "time"].max() - p.loc[last, "time"].min()).days / 7
    rows = {}
    for name, thr in strategies.items():
        alert = (p.loc[last, "y_pred"] >= thr[last]).to_numpy()
        m = binary_metrics(truth, alert)
        q = p.loc[last].assign(alert=alert, truth=truth)
        summer = q[q["season"] == "Yaz"]
        st_recall = q[q["truth"]].groupby("station", observed=True)["alert"].mean()
        rows[name] = {
            "recall": m["recall"], "precision": m["precision"], "F1": m["f1"],
            "yaz precision": binary_metrics(summer["truth"], summer["alert"])["precision"],
            "en düşük istasyon recall": st_recall.min(),
            "uyarı saati / ist.-hafta": m["uyarı_saati"] / (weeks * q["station"].nunique()),
        }
    out = pd.DataFrame(rows).T
    out.index.name = "strateji"
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
        "## Eşik stratejileri (istasyon / mevsim)",
        "",
        "Aynı walk-forward kural, grup başına uygulanır; geçmişte grup için "
        f"{MIN_GROUP_ALERTS}'den az uyarı varsa genel eşik kullanılır.",
        "",
        to_markdown(compare_strategies(preds, sorted(thresholds)), ".3f"),
        "",
        "## Canlı sistem eşikleri (istasyon bazlı)",
        "",
        "Karar: istasyon bazlı eşik (en düşük istasyon recall'ü 0,39 → 0,71). Tüm "
        f"{preds['fold'].nunique()} pencerenin tahminlerinden seçildi; genel (yedek) eşik "
        f"**{final} µg/m³**. Dosya: `{THRESHOLD_PATH.relative_to(ROOT).as_posix()}`.",
        "",
        to_markdown(pd.Series(station_thresholds(preds), name="eşik (µg/m³)")
                    .rename_axis("istasyon"), ".1f"),
        "",
    ])


def station_thresholds(preds: pd.DataFrame, target: float = TARGET_RECALL,
                       min_alerts: int = MIN_GROUP_ALERTS) -> dict[str, float]:
    """Canlı sistem için istasyon başına eşik: tüm tahminlerden, yetersiz örnekte genel eşik."""
    fallback = threshold_for_recall(preds["y_true"], preds["y_pred"], target)
    out = {}
    for st, g in preds.groupby("station", observed=True):
        enough = exceeds(g["y_true"]).sum() >= min_alerts
        out[str(st)] = (threshold_for_recall(g["y_true"], g["y_pred"], target)
                        if enough else fallback)
    return out


def load_thresholds(path=THRESHOLD_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def decision_threshold(station: str, config: dict | None = None) -> float:
    """Bir istasyon için uyarı karar eşiği; tanımsız istasyonda genel eşik."""
    config = config or load_thresholds()
    return float(config["stations"].get(station, config["default_threshold_ugm3"]))


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
        "model": MODEL, "horizon_h": 24, "strategy": "station",
        "default_threshold_ugm3": final, "stations": station_thresholds(preds),
        "official_threshold_ugm3": OFFICIAL, "target_recall": TARGET_RECALL,
        "min_group_alerts": MIN_GROUP_ALERTS,
        "calibrated_on": f"{preds['time'].min():%Y-%m-%d} → {preds['time'].max():%Y-%m-%d}",
        "created": date.today().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(preds, thresholds, final, len(eval_folds)) + "\n",
                           encoding="utf-8")
    print("walk-forward eşikler:", thresholds)
    print(f"canlı eşik: {final}")
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
