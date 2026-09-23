"""İstasyon hedefli geri test tahminlerinin hata analizi (Faz 4.3).

Kullanım:
    python -m havauyari.evaluation.error_analysis
    -> reports/hata_analizi_istasyon_h24.md, reports/figures/4_*.png

Girdi: data/processed/preds_station_h24.parquet (models.train_station çıktısı).

Not: Buradaki eşik tablosu yalnızca TANIMLAYICIDIR (test verisi üzerinde). Canlıda kullanılacak
eşik, test dönemini görmeden seçilir (Faz 4.4).
"""

from __future__ import annotations

from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from havauyari.alerts.aqi import ALERT_INDEX, threshold_concentration  # noqa: E402
from havauyari.config import PROCESSED_DIR, ROOT  # noqa: E402
from havauyari.evaluation.metrics import exceeds  # noqa: E402
from havauyari.reporting import to_markdown  # noqa: E402

PREDS_PATH = PROCESSED_DIR / "preds_station_h24.parquet"
REPORT_PATH = ROOT / "reports" / "hata_analizi_istasyon_h24.md"
FIG_DIR = ROOT / "reports" / "figures"

MAIN, OPT = "lgbm_gercekci", "lgbm_iyimser"
COMPARE = [MAIN, "persistence", "cams_raw"]
VALUE_BINS = [0, 10, 20, 35.5, 55.5, np.inf]
VALUE_LABELS = ["0–10", "10–20", "20–35,5", "35,5–55,5", "≥55,5"]
DECISION_THRESHOLDS = [20, 22.5, 25, 27.5, 30, 32.5, 35.5, 40]


def load(path=PREDS_PATH) -> pd.DataFrame:
    p = pd.read_parquet(path)
    p["err"] = p["y_pred"] - p["y_true"]
    p["abs_err"] = p["err"].abs()
    return p


def wide(p: pd.DataFrame) -> pd.DataFrame:
    """(time, station) başına tek satır; her model bir sütun."""
    w = p.pivot_table(index=["time", "station"], columns="model", values="y_pred", observed=True)
    truth = p.drop_duplicates(["time", "station"]).set_index(["time", "station"])
    return w.join(truth[["y_true", "target_time", "season", "city"]])


# ---------------------------------------------------------------------------------------------
# Analizler
# ---------------------------------------------------------------------------------------------
def by_value_bin(p: pd.DataFrame) -> pd.DataFrame:
    """Gerçek değer aralığına göre MAE ve sapma: zirveler bastırılıyor mu?"""
    q = p[p["model"].isin(COMPARE)].copy()
    q["aralık"] = pd.cut(q["y_true"], VALUE_BINS, labels=VALUE_LABELS, right=False)
    g = q.groupby(["aralık", "model"], observed=True).agg(
        MAE=("abs_err", "mean"), sapma=("err", "mean"), n=("err", "size")).unstack("model")
    out = pd.DataFrame({
        "saat sayısı": g[("n", MAIN)],
        **{f"MAE {m}": g[("MAE", m)] for m in COMPARE},
        **{f"sapma {m}": g[("sapma", m)] for m in COMPARE},
    })
    out.index.name = "gerçek PM2.5"
    return out


def by_hour(p: pd.DataFrame) -> pd.DataFrame:
    q = p[p["model"] == MAIN]
    h = q["target_time"].dt.hour
    out = q.groupby(h).agg(MAE=("abs_err", "mean"), sapma=("err", "mean"),
                           gerçek_ort=("y_true", "mean")).loc[list(range(0, 24, 3))]
    out.index = [f"{x:02d}:00" for x in out.index]
    out.index.name = "hedef saat"
    return out


def station_season(p: pd.DataFrame) -> pd.DataFrame:
    q = p[p["model"] == MAIN]
    t = q.pivot_table(index="station", columns="season", values="abs_err", aggfunc="mean",
                      observed=True)
    t = t[[s for s in ["Kış", "İlkbahar", "Yaz", "Sonbahar"] if s in t.columns]]
    t["tümü"] = q.groupby("station", observed=True)["abs_err"].mean()
    t.index.name = "istasyon"
    return t


def missed_alerts(w: pd.DataFrame) -> pd.DataFrame:
    """Kaçırılan uyarılarda tahmin eşiğe ne kadar yaklaşmıştı?"""
    alert = exceeds(w["y_true"])
    rows = {}
    for m in COMPARE:
        missed = w.loc[alert & ~exceeds(w[m]), m]
        rows[m] = {"gerçek uyarı": int(alert.sum()), "kaçırılan": len(missed),
                   "kaçırılanlarda medyan tahmin": missed.median(),
                   "tahmin ≥ 30 olan kaçırılan %": (missed >= 30).mean() * 100,
                   "tahmin ≥ 25 olan kaçırılan %": (missed >= 25).mean() * 100}
    out = pd.DataFrame(rows).T
    out.index.name = "model"
    return out


def onset_vs_continuing(w: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    """Uyarılar ikiye ayrılır: t anında zaten uyarı var (süren) / yok (YENİ başlayan).

    Erken uyarının asıl değeri yeni başlayan uyarıları önceden görmektir; persistence bunları
    tanım gereği kaçırır.
    """
    # t anındaki gözlem = persistence tahmini (istasyonun t anındaki değeri)
    now_alert = exceeds(w["persistence"])
    target_alert = exceeds(w["y_true"])
    rows = {}
    for label, mask in [("YENİ başlayan", target_alert & ~now_alert),
                        ("süren", target_alert & now_alert)]:
        rows[label] = {"uyarı saati": int(mask.sum()),
                       **{f"recall {m}": exceeds(w.loc[mask, m]).mean() for m in COMPARE}}
    out = pd.DataFrame(rows).T
    out.index.name = "uyarı türü"
    return out


def threshold_tradeoff(w: pd.DataFrame, model: str = MAIN) -> pd.DataFrame:
    """Karar eşiği (tahmin ≥ eşik ise uyar) değiştikçe recall/precision. TANIMLAYICI."""
    truth = exceeds(w["y_true"])
    n_station_weeks = w.index.get_level_values("station").nunique() * (
        (w["target_time"].max() - w["target_time"].min()).days / 7)
    rows = {}
    for thr in DECISION_THRESHOLDS:
        pred = w[model] >= thr
        tp = int((pred & truth).sum())
        rows[thr] = {"recall": tp / truth.sum(), "precision": tp / max(pred.sum(), 1),
                     "uyarı saati / istasyon-hafta": pred.sum() / n_station_weeks}
    out = pd.DataFrame(rows).T
    out["F1"] = 2 * out["recall"] * out["precision"] / (out["recall"] + out["precision"])
    out.index.name = "karar eşiği (µg/m³)"
    return out


def worst_days(w: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    d = w.assign(gün=w["target_time"].dt.date, err=(w[MAIN] - w["y_true"]).abs())
    d = d.reset_index()
    g = d.groupby(["station", "gün"], observed=True).agg(
        MAE=("err", "mean"), gerçek_ort=("y_true", "mean"), gerçek_maks=("y_true", "max"),
        tahmin_ort=(MAIN, "mean"), cams_ort=("cams_raw", "mean"), saat=("err", "size"))
    g = g[g["saat"] >= 12].sort_values("MAE", ascending=False).head(n).drop(columns="saat")
    g.index = [f"{st} · {day:%Y-%m-%d}" for st, day in g.index]
    g.index.name = "istasyon · gün"
    return g


# ---------------------------------------------------------------------------------------------
# Grafikler
# ---------------------------------------------------------------------------------------------
def plot_calibration(w: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(6.5, 5))
    bins = np.arange(0, 125, 5)
    mid = (bins[:-1] + bins[1:]) / 2
    for m, color in [(MAIN, "#1f77b4"), ("persistence", "#7f7f7f"), ("cams_raw", "#d62728")]:
        b = pd.cut(w["y_true"], bins)
        mean_pred = w.groupby(b, observed=False)[m].mean().to_numpy()
        ax.plot(mid, mean_pred, marker="o", ms=3, label=m, color=color)
    ax.plot([0, 120], [0, 120], ls="--", color="black", lw=1, label="kusursuz")
    ax.axhline(threshold_concentration(ALERT_INDEX), color="orange", lw=1, ls=":")
    ax.axvline(threshold_concentration(ALERT_INDEX), color="orange", lw=1, ls=":")
    ax.set(xlim=(0, 120), ylim=(0, 120), xlabel="gerçek PM2.5 (µg/m³, 5'lik aralık)",
           ylabel="ortalama tahmin (µg/m³)",
           title="Gerçek değere göre ortalama tahmin (24 s)")
    ax.legend()
    fig.tight_layout()
    name = "4_kalibrasyon.png"
    fig.savefig(FIG_DIR / name, dpi=120)
    plt.close(fig)
    return name


def plot_tradeoff(w: pd.DataFrame) -> str:
    truth = exceeds(w["y_true"])
    fig, ax = plt.subplots(figsize=(6.5, 5))
    thr = np.arange(10, 60, 0.5)
    for m, color in [(MAIN, "#1f77b4"), (OPT, "#9ecae1")]:
        rec = [((w[m] >= t) & truth).sum() / truth.sum() for t in thr]
        prec = [((w[m] >= t) & truth).sum() / max((w[m] >= t).sum(), 1) for t in thr]
        ax.plot(rec, prec, label=m, color=color)
        i = int(np.argmin(np.abs(thr - 35.5)))
        ax.scatter(rec[i], prec[i], color=color, zorder=3)
    for m, color in [("persistence", "#7f7f7f"), ("cams_raw", "#d62728"),
                     ("cams_scaled", "#ff9896")]:
        p = exceeds(w[m])
        ax.scatter((p & truth).sum() / truth.sum(), (p & truth).sum() / p.sum(),
                   color=color, marker="s", label=m, zorder=3)
    ax.set(xlabel="recall (yakalanan uyarı oranı)", ylabel="precision (doğru uyarı oranı)",
           xlim=(0, 1), ylim=(0, 1), title="Uyarı: yakalama / isabet dengesi (24 s)")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    name = "4_uyari_dengesi.png"
    fig.savefig(FIG_DIR / name, dpi=120)
    plt.close(fig)
    return name


# ---------------------------------------------------------------------------------------------
def build_report(p: pd.DataFrame) -> str:
    w = wide(p)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cal, trade = plot_calibration(w), plot_tradeoff(w)
    return "\n".join([
        "# Hata Analizi: İstasyon Hedefi, 24 Saat",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: "
        "`python -m havauyari.evaluation.error_analysis` · Ana model: `lgbm_gercekci`_",
        "",
        "## 1. Gerçek değere göre hata",
        "",
        "Sapma = tahmin − gerçek. Negatif sapma yüksek değerlerde düşük tahmin demektir.",
        "",
        to_markdown(by_value_bin(p), ".2f"),
        "",
        f"![Kalibrasyon](figures/{cal})",
        "",
        "## 2. Yeni başlayan ve süren uyarılar",
        "",
        "Yeni başlayan: t anında istasyonda uyarı yok, t+24'te var. Persistence bunları tanım "
        "gereği kaçırır; erken uyarının asıl değeri burada.",
        "",
        to_markdown(onset_vs_continuing(w), ".3f"),
        "",
        "## 3. Kaçırılan uyarılar",
        "",
        to_markdown(missed_alerts(w), ".1f"),
        "",
        "## 4. Karar eşiği dengesi (tanımlayıcı)",
        "",
        "Test verisi üzerinde hesaplanmıştır; eşik seçimi için KULLANILMAZ (Faz 4.4'te test "
        "dönemi görülmeden seçilecek).",
        "",
        to_markdown(threshold_tradeoff(w), ".3f"),
        "",
        f"![Uyarı dengesi](figures/{trade})",
        "",
        "## 5. Hedef saate göre hata",
        "",
        to_markdown(by_hour(p), ".2f"),
        "",
        "## 6. İstasyon × mevsim MAE",
        "",
        to_markdown(station_season(p), ".2f"),
        "",
        "## 7. En kötü 10 istasyon-gün (≥ 12 saat veri)",
        "",
        to_markdown(worst_days(w), ".1f"),
        "",
    ])


CURVES_PATH = ROOT / "reports" / "perf_curves.json"


def export_curves(w: pd.DataFrame) -> dict:
    """Panonun tema uyumlu grafikleri için özet eğriler (ham tahminler olmadan çizilebilsin)."""
    truth = exceeds(w["y_true"])
    thr = np.round(np.arange(10, 60.01, 1.0), 1)
    pr = {}
    for m in (MAIN, OPT):
        rec = [float(((w[m] >= t) & truth).sum() / truth.sum()) for t in thr]
        prec = [float(((w[m] >= t) & truth).sum() / max((w[m] >= t).sum(), 1)) for t in thr]
        pr[m] = {"threshold": thr.tolist(), "recall": rec, "precision": prec}
    points = {}
    for m in ("persistence", "cams_raw", "cams_scaled"):
        p = exceeds(w[m])
        points[m] = {"recall": float((p & truth).sum() / truth.sum()),
                     "precision": float((p & truth).sum() / p.sum())}
    bins = np.arange(0, 125, 5)
    b = pd.cut(w["y_true"], bins)
    calib = {"true_mid": ((bins[:-1] + bins[1:]) / 2).tolist()}
    for m in (MAIN, "persistence", "cams_raw"):
        calib[m] = [None if pd.isna(v) else round(float(v), 2)
                    for v in w.groupby(b, observed=False)[m].mean()]
    return {"pr": pr, "points": points, "calibration": calib}


def main() -> None:
    import json

    p = load()
    REPORT_PATH.write_text(build_report(p) + "\n", encoding="utf-8")
    CURVES_PATH.write_text(json.dumps(export_curves(wide(p))), encoding="utf-8")
    print(f"[ok] {REPORT_PATH}, {CURVES_PATH}")


if __name__ == "__main__":
    main()
