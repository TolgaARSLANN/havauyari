"""Final model (Faz 4.7) ve açıklanabilirlik (Faz 4.6).

Final model: istasyon hedefli, 24 saat, gerçekçi özellik seti (CAMS'ın gelecek değerleri yok),
L2 kaybı (Faz 4.2 deneyinde en iyisi), tüm veriyle eğitilir.

Açıklanabilirlik: LightGBM'in yerleşik `pred_contrib` çıktısı (TreeSHAP ile aynı değerler); her
tahmin = taban değer + özellik katkılarının toplamı. Ek bağımlılık gerekmez.

Kullanım:
    python -m havauyari.models.final
    -> models/lgbm_station_h24.txt (git dışı), models/model_card.json,
       reports/aciklanabilirlik_h24.md, reports/figures/4_shap_*.png
"""

from __future__ import annotations

import json
from datetime import date

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from havauyari.config import MODELS_DIR, ROOT  # noqa: E402
from havauyari.features.build import STATION_TARGET, feature_columns  # noqa: E402
from havauyari.models.train import LGBM_PARAMS  # noqa: E402
from havauyari.reporting import to_markdown  # noqa: E402

HORIZON = 24
TARGET = f"target_h{HORIZON}"
MODEL_PATH = MODELS_DIR / f"lgbm_station_h{HORIZON}.txt"
CARD_PATH = MODELS_DIR / "model_card.json"
REPORT_PATH = ROOT / "reports" / f"aciklanabilirlik_h{HORIZON}.md"
FIG_DIR = ROOT / "reports" / "figures"
FAMILIES_PATH = ROOT / "reports" / "feature_families.json"
EXPLAIN_FROM = "2025-09-23"   # açıklamalar son 12 ayın (test dönemi) satırları üzerinde


# ---------------------------------------------------------------------------------------------
# Özellik aileleri (okunabilir açıklama için)
# ---------------------------------------------------------------------------------------------
FAMILIES = [
    ("hava tahmini (o gün yayımlanan)", lambda c: c.startswith("fc_")),
    ("istasyon PM2.5 geçmişi", lambda c: c.startswith(STATION_TARGET)),
    ("istasyon PM10", lambda c: c.startswith("station_pm10")),
    ("CAMS PM2.5 ve oranı", lambda c: c.startswith("pm2_5") or c.startswith("pm_ratio")),
    ("CAMS diğer kirleticiler", lambda c: c.split("_lag")[0].split("_roll")[0] in {
        "pm10", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide", "ozone"}),
    ("takvim ve hedef zamanı", lambda c: c.startswith("tgt_") or c in {
        "hour", "dayofweek", "month", "is_weekend", "is_holiday", "hour_sin", "hour_cos",
        "month_sin", "month_cos"}),
    ("istasyon / şehir kimliği", lambda c: c in {"station_code", "city_code"}),
]


def family_of(col: str) -> str:
    for name, rule in FAMILIES:
        if rule(col):
            return name
    return "meteoroloji gözlemi (ERA5)"


# ---------------------------------------------------------------------------------------------
def train_final(feats: pd.DataFrame) -> tuple[lgb.LGBMRegressor, list[str]]:
    data = feats.dropna(subset=[TARGET])
    cols = feature_columns(data, realistic=True)
    model = lgb.LGBMRegressor(**LGBM_PARAMS)
    model.fit(data[cols], data[TARGET])
    return model, cols


def contributions(booster: lgb.Booster, X: pd.DataFrame) -> pd.DataFrame:
    """Satır başına özellik katkıları; son sütun 'taban' (beklenen değer). Toplam = tahmin."""
    contrib = booster.predict(X, pred_contrib=True)
    return pd.DataFrame(contrib, index=X.index, columns=[*X.columns, "taban"])


def explain_row(booster: lgb.Booster, row: pd.DataFrame, top: int = 8) -> pd.DataFrame:
    """Tek tahminin açıklaması: en büyük mutlak katkılı özellikler, değerleriyle."""
    c = contributions(booster, row).iloc[0]
    base = c.pop("taban")
    top_c = c.reindex(c.abs().sort_values(ascending=False).index[:top])
    out = pd.DataFrame({"değer": row.iloc[0][top_c.index], "katkı (µg/m³)": top_c})
    out.loc["diğer özellikler", "katkı (µg/m³)"] = c.drop(top_c.index).sum()
    out.loc["taban (ortalama)", "katkı (µg/m³)"] = base
    out.index.name = "özellik"
    return out


# ---------------------------------------------------------------------------------------------
def _bar(series: pd.Series, title: str, name: str, color: str = "#1f77b4") -> str:
    s = series.sort_values()
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(s) + 1.2))
    ax.barh(s.index, s.to_numpy(), color=color)
    ax.set(title=title, xlabel="ortalama |katkı| (µg/m³)")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=120)
    plt.close(fig)
    return name


def _local_plot(expl: pd.DataFrame, title: str, name: str) -> str:
    # "diğer" toplamı tabloda gösterilir; grafikte en etkili özellikler okunur kalsın diye yok
    e = expl.drop(index=["taban (ortalama)", "diğer özellikler"])["katkı (µg/m³)"][::-1]
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(e) + 1.2))
    ax.barh(e.index, e.to_numpy(), color=["#d62728" if v > 0 else "#2ca02c" for v in e])
    ax.axvline(0, color="black", lw=0.8)
    ax.set(title=title, xlabel="tahmine katkı (µg/m³)  —  kırmızı: artırıyor, yeşil: azaltıyor")
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=120)
    plt.close(fig)
    return name


def build_report(booster: lgb.Booster, feats: pd.DataFrame, cols: list[str]) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    recent = feats.loc[EXPLAIN_FROM:].dropna(subset=[TARGET])
    sample = recent.sample(min(30_000, len(recent)), random_state=0)
    contrib = contributions(booster, sample[cols]).drop(columns="taban")
    importance = contrib.abs().mean().sort_values(ascending=False)
    family = importance.groupby(importance.index.map(family_of)).sum().sort_values(ascending=False)
    family_share = (family / family.sum() * 100).rename("pay %")

    top20 = importance.head(20)
    f1 = _bar(top20, "En etkili 20 özellik (son 12 ay, 30.000 tahmin)", "4_shap_ozellik.png")
    f2 = _bar(family, "Özellik ailelerinin toplam katkısı", "4_shap_aile.png", "#ff7f0e")

    # Yön: özelliğin yüksek değerleri tahmini artırıyor mu?
    direction = {}
    for c in top20.index:
        x = sample[c]
        if x.nunique() > 2:
            direction[c] = np.corrcoef(x.fillna(x.median()), contrib[c])[0, 1]
    top_table = pd.DataFrame({"aile": top20.index.map(family_of),
                              "ort. |katkı|": top20,
                              "değer ↑ → tahmin": pd.Series(direction).reindex(top20.index)
                              .map(lambda r: "" if pd.isna(r) else ("artırır" if r > 0.2 else
                                                                    "azaltır" if r < -0.2 else
                                                                    "karışık"))})
    top_table.index.name = "özellik"

    # Yerel örnek: son 12 ayın en yüksek tahminli kış saati (Bursa)
    bursa_winter = recent[(recent["station"] == "bursa") & recent.index.month.isin([12, 1, 2])]
    pred = booster.predict(bursa_winter[cols])
    t = bursa_winter.index[int(np.argmax(pred))]
    row = bursa_winter.loc[[t], cols]
    expl = explain_row(booster, row, top=10)
    actual = bursa_winter.loc[t, TARGET]
    f3 = _local_plot(expl, f"Bursa, {t:%Y-%m-%d %H:%M} için 24 s sonrası tahmini",
                     "4_shap_ornek.png")

    FAMILIES_PATH.write_text(json.dumps(
        {"family_share_pct": family_share.round(2).to_dict(),
         "top_features": top20.round(3).to_dict()}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    fam_view = pd.DataFrame({"toplam ort. |katkı|": family, "pay %": family_share})
    fam_view.index.name = "aile"
    return "\n".join([
        "# Açıklanabilirlik: Final Model, 24 Saat",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Üreten: `python -m havauyari.models.final`_",
        "",
        "Katkılar LightGBM `pred_contrib` (TreeSHAP) ile hesaplandı: her tahmin = taban değer + "
        "özellik katkıları. Örnek: son 12 aydan 30.000 tahmin. Final model tüm veriyle "
        "eğitildiği için bu tablo modelin *neye dayandığını* gösterir, performans ölçüsü değildir.",
        "",
        "## Özellik aileleri",
        "",
        to_markdown(fam_view, ".2f"),
        "",
        f"![Aileler](figures/{f2})",
        "",
        "## En etkili 20 özellik",
        "",
        to_markdown(top_table, ".2f"),
        "",
        f"![Özellikler](figures/{f1})",
        "",
        "## Örnek açıklama",
        "",
        f"Bursa istasyonu, {t:%Y-%m-%d %H:%M} anında verilen 24 saat sonrası tahmini: "
        f"**{pred.max():.1f} µg/m³** (gerçekleşen {actual:.1f}).",
        "",
        to_markdown(expl, ".2f"),
        "",
        f"![Örnek](figures/{f3})",
        "",
    ])


REGISTRY_PATH = MODELS_DIR / "stations.json"


def write_station_registry() -> list[dict]:
    """Servisin kullanacağı istasyon listesi (SİM kimliği, ad, şehir, koordinat) repoya yazılır."""
    from havauyari.data.fetch_sim import SURVEY_PATH, select_stations, slugify

    selected = select_stations(pd.read_csv(SURVEY_PATH))
    registry = [{"slug": slugify(r["name"]), "sim_id": r["id"], "name": r["name"],
                 "city": r["city"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                 "area_type": r["area_type"], "source_type": r["source_type"]}
                for _, r in selected.iterrows()]
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return registry


def main() -> None:
    from havauyari.models.train_station import prepare

    write_station_registry()

    feats = prepare(HORIZON)
    model, cols = train_final(feats)
    booster = model.booster_
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(MODEL_PATH))

    data = feats.dropna(subset=[TARGET])
    card = {
        "model": "lgbm_gercekci", "horizon_h": HORIZON, "target": "SİM istasyon PM2.5 (µg/m³)",
        "objective": "L2 (regression)", "params": LGBM_PARAMS,
        "trained_on": f"{data.index.min():%Y-%m-%d} → {data.index.max():%Y-%m-%d}",
        "n_rows": int(len(data)), "stations": sorted(map(str, data["station"].unique())),
        "station_codes": {str(s): int(c) for s, c in
                          data[["station", "station_code"]].drop_duplicates().values},
        "city_codes": {str(s): int(c) for s, c in
                       data[["city", "city_code"]].drop_duplicates().values},
        "features": cols,
        "backtest_12m": {"mae": 6.78, "rmse": 10.78, "cams_raw_mae": 12.95,
                         "alert_recall_station_thresholds": 0.798,
                         "alert_precision_station_thresholds": 0.548,
                         "interval_80_coverage": 0.829,
                         "reports": ["reports/backtest_istasyon_h24.md",
                                     "reports/uyari_esigi_h24.md",
                                     "reports/tahmin_araligi_h24.md"]},
        "alert_thresholds": "models/alert_threshold.json",
        "prediction_interval": "models/prediction_interval.json",
        "model_file": MODEL_PATH.relative_to(ROOT).as_posix(),
        "created": date.today().isoformat(),
    }
    CARD_PATH.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(build_report(booster, feats, cols) + "\n", encoding="utf-8")
    print(f"[ok] model: {MODEL_PATH} ({MODEL_PATH.stat().st_size / 1e6:.1f} MB), "
          f"{len(cols)} özellik, {len(data):,} satır")
    print(f"[ok] {REPORT_PATH}")


if __name__ == "__main__":
    main()
