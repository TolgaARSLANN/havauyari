"""HavaUyarı panosu (Faz 6).

Çalıştırma:
    streamlit run src/havauyari/ui/app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from havauyari.config import ROOT
from havauyari.serving.service import DataUnavailable
from havauyari.ui import state
from havauyari.ui.components import (
    ADVICE,
    CATEGORY_TEXT_COLORS,
    CITY_LABELS,
    DISCLAIMER,
    category_color,
    explanation_figure,
    explanation_sentence,
    forecast_figure,
    map_figure,
    tr_num,
)

FIG_DIR = ROOT / "reports" / "figures"
REPO_URL = "https://github.com/TolgaARSLANN/havauyari"

st.set_page_config(page_title="HavaUyarı · PM2.5 erken uyarı", page_icon="🌫️", layout="wide")


@st.cache_resource(show_spinner=False)
def get_service():
    return state.SERVICE_FACTORY()


def load_forecasts(service) -> tuple[dict, dict]:
    ok, errors = {}, {}
    for slug in service.a.stations:
        try:
            ok[slug] = service.forecast(slug)
        except DataUnavailable as e:
            errors[slug] = str(e)
    return ok, errors


def badge(category: str, text: str | None = None) -> str:
    return (f"<span style='background:{category_color(category)};"
            f"color:{CATEGORY_TEXT_COLORS.get(category, '#000')};padding:3px 10px;"
            f"border-radius:12px;font-weight:600'>{text or category}</span>")


def station_label(s: dict) -> str:
    """İstasyon adı şehri zaten içeriyor (örn. 'İzmir - Konak'); 'Bursa' gibi tek sözcüklü
    adlarda şehir adı istasyon adıyla aynı."""
    city = CITY_LABELS.get(s["city"], s["city"])
    return s["name"] if s["name"].startswith(city) else f"{city} · {s['name']}"


# ---------------------------------------------------------------------------------------------
st.title("🌫️ HavaUyarı")
st.caption("Türkiye'deki hava kalitesi istasyonlarında **24 saat sonra ölçülecek PM2.5** "
           "tahmini ve erken uyarı")

try:
    service = get_service()
except FileNotFoundError as e:
    st.error(f"Model yüklenemedi: {e}")
    st.stop()

with st.spinner("Canlı veriler alınıyor ve tahminler hesaplanıyor…"):
    forecasts, errors = load_forecasts(service)

tab_overview, tab_station, tab_model, tab_about = st.tabs(
    ["Genel bakış", "İstasyon", "Model performansı", "Hakkında"])

# --- Genel bakış -----------------------------------------------------------------------------
with tab_overview:
    if forecasts:
        any_f = next(iter(forecasts.values()))
        issued, target = pd.Timestamp(any_f["issued_at"]), pd.Timestamp(any_f["target_time"])
        n_alert = sum(f["alert"]["is_alert"] for f in forecasts.values())
        n_risk = sum(f["alert"]["risk"] for f in forecasts.values())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tahmin zamanı", f"{issued:%d.%m %H:%M}")
        c2.metric("Hedef zaman", f"{target:%d.%m %H:%M}")
        c3.metric("Uyarı verilen istasyon", f"{n_alert} / {len(forecasts)}")
        c4.metric("Uyarı riski olan istasyon", f"{n_risk} / {len(forecasts)}")

        rows = []
        for slug, f in forecasts.items():
            s = service.a.stations[slug]
            rows.append({"name": station_label(s), "lat": s["lat"], "lon": s["lon"],
                         "pm25": f["pm25"], "category": f["category"],
                         "is_alert": f["alert"]["is_alert"], "risk": f["alert"]["risk"]})
        st.plotly_chart(map_figure(rows), width="stretch")

        table = pd.DataFrame([{
            "İstasyon": station_label(service.a.stations[slug]),
            "Şu an (µg/m³)": f["latest_measurement"]["pm25"],
            "24 s sonra (µg/m³)": f["pm25"],
            "%80 aralık": f"{f['interval_80']['low']:.0f}–{f['interval_80']['high']:.0f}",
            "Kategori": f["category"],
            "Uyarı": "⚠️ evet" if f["alert"]["is_alert"] else "hayır",
            "Risk": "evet" if f["alert"]["risk"] else "",
        } for slug, f in forecasts.items()])
        st.dataframe(table, hide_index=True, width="stretch")
    for slug, msg in errors.items():
        st.warning(f"{station_label(service.a.stations[slug])}: {msg}")
    st.caption("**Uyarı:** tahmin, istasyonun karar eşiğini aşıyor (eşikler uyarıların en az "
               "%80'ini yakalayacak şekilde geçmiş veriden seçildi). **Risk:** %80 aralığın üst "
               "sınırı resmî eşik 35,5 µg/m³'ü aşıyor.")

# --- İstasyon --------------------------------------------------------------------------------
with tab_station:
    options = [s for s in service.a.stations if s in forecasts]
    if not options:
        st.info("Şu an tahmin üretilebilen istasyon yok.")
    else:
        slug = st.selectbox("İstasyon", options,
                            format_func=lambda x: station_label(service.a.stations[x]))
        f = forecasts[slug]
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"#### {pd.Timestamp(f['target_time']):%d.%m.%Y %H:%M} için tahmin")
            st.markdown(f"<div style='font-size:3rem;font-weight:700'>{f['pm25']:.0f} "
                        "<span style='font-size:1.2rem'>µg/m³</span></div>",
                        unsafe_allow_html=True)
            st.markdown(badge(f["category"], f"{f['category']} · AQI {f['aqi']}"),
                        unsafe_allow_html=True)
            st.markdown(f"**%80 olasılıkla:** {f['interval_80']['low']:.0f} – "
                        f"{f['interval_80']['high']:.0f} µg/m³")
            a = f["alert"]
            if a["is_alert"]:
                st.error(f"⚠️ Uyarı: tahmin, istasyon karar eşiğini "
                         f"({tr_num(a['decision_threshold'])}) aşıyor.")
            elif a["risk"]:
                st.warning("Uyarı riski: aralığın üst sınırı resmî eşiği (35,5) aşıyor.")
            else:
                st.success("Uyarı yok.")
            st.markdown(f"**Ne yapmalı?** {ADVICE[f['category']]}")
            lm = f["latest_measurement"]
            if lm["time"] is not None:
                st.caption(f"Son ölçüm: {tr_num(lm['pm25'])} µg/m³ "
                           f"({pd.Timestamp(lm['time']):%d.%m %H:%M})")
        with right:
            st.plotly_chart(forecast_figure(f), width="stretch")
            traj = pd.DataFrame(f["trajectory"]).dropna(subset=["actual"])
            if len(traj) >= 12:
                mae = (traj["pm25"] - traj["actual"]).abs().mean()
                st.caption(f"Canlı kontrol: son {len(traj)} saatte 24 s önceden verilen "
                           f"tahminlerin ortalama hatası **{tr_num(mae)} µg/m³** "
                           "(geri testte 12 aylık ortalama 6,8).")

        st.markdown("#### Bu tahmin neden böyle?")
        st.markdown(explanation_sentence(f["explanation"]))
        st.plotly_chart(explanation_figure(f["explanation"]), width="stretch")
        st.caption(f"Modelin ortalama tahmini {tr_num(f['explanation']['base_value'])} µg/m³; "
                   "çubuklar bu istasyon ve saat için tahmini ne kadar yukarı (kırmızı) veya "
                   "aşağı (yeşil) çektiğini gösterir. Diğer özelliklerin toplam katkısı: "
                   f"{tr_num(f['explanation']['other_features'], sign=True)} µg/m³.")

# --- Model performansı -----------------------------------------------------------------------
with tab_model:
    bt = service.a.card.get("backtest_12m", {})
    st.markdown("Son 12 ay (2025-09 → 2026-09) walk-forward geri test; 8 istasyon, "
                "eşikler ve aralıklar test dönemi görülmeden seçildi.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ortalama hata (MAE)", f"{tr_num(bt.get('mae', float('nan')), 2)} µg/m³")
    c1.caption(f"Ham CAMS: {tr_num(bt.get('cams_raw_mae', float('nan')), 2)} µg/m³")
    c2.metric("Yakalanan uyarı", f"%{bt.get('alert_recall_station_thresholds', 0) * 100:.0f}")
    c3.metric("Doğru uyarı oranı",
              f"%{bt.get('alert_precision_station_thresholds', 0) * 100:.0f}")
    c4.metric("%80 aralık kapsaması",
              f"%{tr_num(bt.get('interval_80_coverage', 0) * 100)}")
    cols = st.columns(2)
    for col, (img, cap) in zip(cols, [
            ("4_uyari_dengesi.png", "Uyarı yakalama / isabet dengesi: model, CAMS ve basit "
                                    "yöntemlerin üstünde"),
            ("4_kalibrasyon.png", "Gerçek değere göre ortalama tahmin: yüksek değerler hâlâ "
                                  "düşük tahmin ediliyor")], strict=True):
        if (FIG_DIR / img).exists():
            col.image(str(FIG_DIR / img), caption=cap, width="stretch")
    if (FIG_DIR / "4_shap_aile.png").exists():
        st.image(str(FIG_DIR / "4_shap_aile.png"),
                 caption="Tahminin kaynakları: istasyon geçmişi ve o gün yayımlanan hava tahmini",
                 width=700)
    st.markdown(f"Ayrıntılı raporlar: [GitHub/reports]({REPO_URL}/tree/main/reports)")

# --- Hakkında --------------------------------------------------------------------------------
with tab_about:
    st.markdown(f"""
**HavaUyarı**, Avrupa'nın CAMS atmosfer modelini yerel istasyon ölçümleri ve o gün yayımlanan
hava tahminiyle düzelterek Türkiye şehirleri için 24 saat önceden PM2.5 tahmini üretir.

- **Hedef:** Çevre, Şehircilik ve İklim Değişikliği Bakanlığı SİM istasyonlarında ölçülen PM2.5
- **Girdiler:** istasyon geçmişi, CAMS (Open-Meteo), 1 gün önce yayımlanmış hava tahmini
  (Open-Meteo Previous Runs), meteoroloji
- **Model:** LightGBM, 99 özellik; eşikler, aralıklar ve sonuçlar walk-forward geri testle
  test dönemi görülmeden seçildi
- **Sınırlamalar:** zirveler hâlâ düşük tahmin ediliyor; 8 istasyon ve tek ufuk (24 saat);
  iki Ankara istasyonunun ölçümleri düşük güvenli

Kaynak kod ve raporlar: [{REPO_URL}]({REPO_URL})
""")
st.divider()
st.caption(DISCLAIMER + " Veri: Çevre, Şehircilik ve İklim Değişikliği Bakanlığı SİM · "
           "Open-Meteo (CAMS, hava tahmini).")
