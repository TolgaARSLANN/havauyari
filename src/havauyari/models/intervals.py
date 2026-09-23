"""Tahmin aralıkları (Faz 4.5): walk-forward conformal, tahmin seviyesine göre koşullu.

Nokta tahmin ("yarın 29 µg/m³") zirveleri bastırdığı için riski gizler. Aralık ("%80 olasılıkla
18–47") belirsizliği ve zirve riskini kullanıcıya dürüstçe gösterir.

Yöntem:
- Kalıntı r = gerçek − tahmin. Hata payı tahmin seviyesiyle büyüdüğü için kalıntılar tahmin
  seviyesi dilimlerine (PRED_BINS) ayrılır; her dilimde r'nin %10 ve %90 değerleri alınır.
- Aralık = [tahmin + q10, tahmin + q90], alt sınır 0'ın altına inmez.
- Walk-forward: her test penceresinin dilim tabloları yalnızca ÖNCEKİ pencerelerin
  kalıntılarından hesaplanır (test dönemi görülmez). Yeniden eğitim gerekmez.

Kullanım:
    python -m havauyari.models.intervals
    -> reports/tahmin_araligi_h24.md, models/prediction_interval.json
"""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd

from havauyari.alerts.threshold import CALIB_PREDS_PATH
from havauyari.config import MODELS_DIR, ROOT
from havauyari.evaluation.metrics import exceeds
from havauyari.reporting import to_markdown

PRED_BINS = [-np.inf, 10, 20, 30, 45, np.inf]
BIN_LABELS = ["<10", "10–20", "20–30", "30–45", "≥45"]
LOWER_Q, UPPER_Q = 0.10, 0.90
REPORT_PATH = ROOT / "reports" / "tahmin_araligi_h24.md"
INTERVAL_PATH = MODELS_DIR / "prediction_interval.json"


def _bin(y_pred) -> pd.Categorical:
    return pd.cut(np.asarray(y_pred, float), PRED_BINS, labels=BIN_LABELS, right=False)


def residual_quantiles(y_true, y_pred, lower: float = LOWER_Q,
                       upper: float = UPPER_Q) -> pd.DataFrame:
    """Tahmin dilimi başına kalıntı (gerçek − tahmin) alt/üst yüzdelikleri."""
    df = pd.DataFrame({"r": np.asarray(y_true, float) - np.asarray(y_pred, float),
                       "bin": _bin(y_pred)}).dropna()
    table = df.groupby("bin", observed=False)["r"].quantile([lower, upper]).unstack()
    table.columns = ["q_low", "q_high"]
    # Boş dilim olursa tüm kalıntıların yüzdelikleri kullanılır
    overall = df["r"].quantile([lower, upper]).to_numpy()
    table["q_low"] = table["q_low"].fillna(overall[0])
    table["q_high"] = table["q_high"].fillna(overall[1])
    table["n"] = df.groupby("bin", observed=False).size()
    return table


def apply_intervals(y_pred, table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    y_pred = np.asarray(y_pred, float)
    b = _bin(y_pred)
    q_low = table["q_low"].reindex(b).to_numpy()
    q_high = table["q_high"].reindex(b).to_numpy()
    return np.clip(y_pred + q_low, 0, None), y_pred + q_high


def walk_forward_intervals(preds: pd.DataFrame, eval_folds: list[int]) -> pd.DataFrame:
    """Değerlendirme pencereleri için aralıklar; yalnızca geçmiş pencerelerin kalıntılarıyla."""
    parts = []
    for k in eval_folds:
        past = preds[preds["fold"] < k]
        if past.empty:
            raise ValueError(f"Pencere {k} için geçmiş tahmin yok")
        table = residual_quantiles(past["y_true"], past["y_pred"])
        cur = preds[preds["fold"] == k].copy()
        cur["lo"], cur["hi"] = apply_intervals(cur["y_pred"], table)
        parts.append(cur)
    out = pd.concat(parts)
    out["kapsandı"] = (out["y_true"] >= out["lo"]) & (out["y_true"] <= out["hi"])
    out["genişlik"] = out["hi"] - out["lo"]
    return out


def coverage_table(q: pd.DataFrame, by: str | None) -> pd.DataFrame:
    g = q if by is None else q.groupby(by, observed=True)
    if by is None:
        return pd.DataFrame({"kapsama": [q["kapsandı"].mean()],
                             "ort. genişlik": [q["genişlik"].mean()],
                             "gerçek > üst sınır": [(q["y_true"] > q["hi"]).mean()],
                             "gerçek < alt sınır": [(q["y_true"] < q["lo"]).mean()]},
                            index=pd.Index(["tümü"], name=""))
    out = g.agg(kapsama=("kapsandı", "mean"), ort_genişlik=("genişlik", "mean"),
                saat=("kapsandı", "size"))
    return out.rename(columns={"ort_genişlik": "ort. genişlik"})


def build_report(q: pd.DataFrame, final: pd.DataFrame) -> str:
    q = q.assign(gerçek_aralık=pd.cut(q["y_true"], [0, 10, 20, 35.5, 55.5, np.inf],
                                      labels=["0–10", "10–20", "20–35,5", "35,5–55,5", "≥55,5"],
                                      right=False))
    truth = exceeds(q["y_true"])
    risk = q["hi"] >= 35.5
    risk_recall = (risk & truth).sum() / truth.sum()
    risk_precision = (risk & truth).sum() / risk.sum()
    example = q[q["y_pred"].between(28, 30)].iloc[0]
    final_view = final.copy()
    final_view.index.name = "tahmin dilimi"
    return "\n".join([
        "# Tahmin Aralıkları: İstasyon Hedefi, 24 Saat",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: `python -m havauyari.models.intervals`"
        " · Model: `lgbm_gercekci`_",
        "",
        "## Yöntem",
        "",
        "Walk-forward conformal: her test penceresi için, yalnızca önceki pencerelerin "
        "kalıntıları (gerçek − tahmin) tahmin seviyesi dilimlerine ayrılır ve "
        f"%{LOWER_Q*100:.0f} / %{UPPER_Q*100:.0f} yüzdelikleri alınır. "
        f"Hedef kapsama %{(UPPER_Q - LOWER_Q) * 100:.0f}. Değerlendirme: son 12 pencere.",
        "",
        "## Genel",
        "",
        to_markdown(coverage_table(q, None), ".3f"),
        "",
        "## Gerçek değere göre kapsama",
        "",
        "Zirvelerde nokta tahmin çok düşük kalıyordu (≥ 55,5'te −23 sapma); aralığın bu riski ne "
        "kadar gösterdiğine bakılır.",
        "",
        to_markdown(coverage_table(q, "gerçek_aralık"), ".3f"),
        "",
        "## Tahmin dilimine göre kapsama",
        "",
        to_markdown(coverage_table(q.assign(dilim=_bin(q["y_pred"])), "dilim"), ".3f"),
        "",
        "## Mevsime ve istasyona göre kapsama",
        "",
        to_markdown(coverage_table(q, "season"), ".3f"),
        "",
        to_markdown(coverage_table(q, "station"), ".3f"),
        "",
        "## Üst sınırın risk göstergesi olarak kullanımı (tanımlayıcı)",
        "",
        f"\"Aralığın üst sınırı ≥ 35,5\" koşulu gerçek uyarıların %{risk_recall*100:.1f}'ini "
        f"kapsıyor (precision %{risk_precision*100:.1f}). Kullanıcıya uyarı kararı yerine "
        "\"uyarı riski var\" bilgisi olarak gösterilebilir.",
        "",
        "Örnek: tahmin "
        f"{example['y_pred']:.1f} µg/m³ → %80 aralık {example['lo']:.1f}–{example['hi']:.1f} "
        f"(gerçekleşen {example['y_true']:.1f}).",
        "",
        "## Canlı sistem tablosu",
        "",
        f"Tüm tahminlerden hesaplandı: `{INTERVAL_PATH.relative_to(ROOT).as_posix()}`",
        "",
        to_markdown(final_view, ".2f"),
        "",
    ])


def main() -> None:
    preds = pd.read_parquet(CALIB_PREDS_PATH)
    folds = sorted(preds["fold"].unique())
    q = walk_forward_intervals(preds, folds[len(folds) // 2:])
    final = residual_quantiles(preds["y_true"], preds["y_pred"])

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    INTERVAL_PATH.write_text(json.dumps({
        "model": "lgbm_gercekci", "horizon_h": 24, "coverage": UPPER_Q - LOWER_Q,
        "pred_bins": [None if np.isinf(b) else b for b in PRED_BINS],
        "bin_labels": BIN_LABELS,
        "q_low": final["q_low"].round(3).tolist(), "q_high": final["q_high"].round(3).tolist(),
        "created": date.today().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(q, final) + "\n", encoding="utf-8")
    print(coverage_table(q, None).round(3).to_string())
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
