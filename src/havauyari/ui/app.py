"""HavaUyarı panosu (Faz 6; tasarım sistemi: ui/theme.py).

Metinler TDK Yazım Kılavuzu'na göre yazılmıştır: saat biçimi "14.00", ay adları yazıyla,
"%80'lik", "resmî", "tahminî", "olağan dışı" vb.

Çalıştırma:
    streamlit run src/havauyari/ui/app.py
"""

from __future__ import annotations

import json
from datetime import timedelta

import pandas as pd
import streamlit as st

from havauyari.config import ROOT
from havauyari.serving.service import DataUnavailable
from havauyari.ui import state
from havauyari.ui.components import (
    ADVICE,
    CITY_LABELS,
    DISCLAIMER,
    calibration_figure,
    callout_html,
    category_chip,
    explanation_figure,
    explanation_sentence,
    families_figure,
    forecast_figure,
    header_html,
    kpi_html,
    legend_html,
    map_figure,
    pr_figure,
    range_html,
    station_card_html,
    tr_datetime,
    tr_num,
    tr_pct,
    tr_short,
)
from havauyari.ui.theme import css, tokens_for

REPORTS = ROOT / "reports"
REPO_URL = "https://github.com/TolgaARSLANN/havauyari"
STALE_AFTER = timedelta(hours=2)
PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"],
               "locale": "tr"}

st.set_page_config(page_title="HavaUyarı · PM2.5 erken uyarı", page_icon=":material/air:",
                   layout="wide", initial_sidebar_state="collapsed")

theme_ctx = getattr(st.context, "theme", None)
T = tokens_for(getattr(theme_ctx, "type", None))
st.markdown(css(T), unsafe_allow_html=True)


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


def load_json(name: str) -> dict | None:
    path = REPORTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def station_label(s: dict) -> str:
    """İstasyon adı çoğunlukla şehri zaten içeriyor ('İzmir - Konak')."""
    city = CITY_LABELS.get(s["city"], s["city"])
    return s["name"] if s["name"].startswith(city) else f"{city} · {s['name']}"


def section(title: str, lead: str | None = None) -> None:
    st.markdown(f'<h2 class="hu-section-title" lang="tr">{title}</h2>', unsafe_allow_html=True)
    if lead:
        st.markdown(f'<p class="hu-lead" lang="tr">{lead}</p>', unsafe_allow_html=True)


def html(fragment: str) -> None:
    st.markdown(fragment, unsafe_allow_html=True)


# --- Veri ------------------------------------------------------------------------------------
header_slot = st.empty()                 # başlık hemen görünür, veri gelince güncellenir
header_slot.markdown(header_html(None, stale=True, t=T), unsafe_allow_html=True)
try:
    service = get_service()
except FileNotFoundError as e:
    st.error(f"Model yüklenemedi: {e}")
    st.stop()

with st.spinner("Canlı ölçümler ve hava tahmini alınıyor, tahminler hesaplanıyor…"):
    forecasts, errors = load_forecasts(service)

issued = pd.Timestamp(next(iter(forecasts.values()))["issued_at"]) if forecasts else None
latest = [pd.Timestamp(f["latest_measurement"]["time"]) for f in forecasts.values()
          if f["latest_measurement"]["time"] is not None]
stale = issued is None or not latest or (issued - max(latest)) > STALE_AFTER
header_slot.markdown(header_html(issued, stale, T), unsafe_allow_html=True)

ordered = sorted(forecasts, key=lambda s: forecasts[s]["pm25"], reverse=True)
tab_overview, tab_station, tab_model, tab_about = st.tabs(
    [":material/map: Genel bakış", ":material/location_on: İstasyon detayı",
     ":material/insights: Model performansı", ":material/info: Hakkında"])

# --- Genel bakış -----------------------------------------------------------------------------
with tab_overview:
    if not forecasts:
        html(callout_html("info", "Şu anda tahmin üretilebilen istasyon yok.", T))
    else:
        f0 = forecasts[ordered[0]]
        n = len(forecasts)
        n_alert = sum(f["alert"]["is_alert"] for f in forecasts.values())
        n_risk = sum(f["alert"]["risk"] and not f["alert"]["is_alert"]
                     for f in forecasts.values())
        cols = st.columns(4)
        cols[0].markdown(kpi_html("Tahmin edilen saat", tr_short(f0["target_time"]),
                                  f"Tahmin zamanı: {tr_short(issued)}", "clock"),
                         unsafe_allow_html=True)
        cols[1].markdown(kpi_html("Uyarı verilen istasyon", f"{n_alert} / {n}",
                                  "Tahmin, karar eşiğini aşıyor.", "alert"),
                         unsafe_allow_html=True)
        cols[2].markdown(kpi_html("Uyarı riski olan istasyon", f"{n_risk} / {n}",
                                  "Aralığın üst sınırı 35,5'i aşıyor.", "eye"),
                         unsafe_allow_html=True)
        cols[3].markdown(kpi_html("En yüksek tahmin",
                                  f"{tr_num(f0['pm25'], 0)} <span class='hu-unit'>µg/m³</span>",
                                  station_label(service.a.stations[ordered[0]]), "activity"),
                         unsafe_allow_html=True)

        section("Harita", "İstasyonlar, yarın bu saat için tahmin edilen hava kalitesi "
                          "kategorisinin rengiyle gösterilir. Ayrıntılar için noktanın üzerine "
                          "gelin.")
        rows = [{"name": station_label(service.a.stations[s]),
                 "lat": service.a.stations[s]["lat"], "lon": service.a.stations[s]["lon"],
                 "pm25": forecasts[s]["pm25"], "category": forecasts[s]["category"],
                 "is_alert": forecasts[s]["alert"]["is_alert"],
                 "risk": forecasts[s]["alert"]["risk"]} for s in ordered]
        html(legend_html())
        st.plotly_chart(map_figure(rows, T), width="stretch", config=PLOT_CONFIG)

        section("İstasyonlar", "İstasyonlar, 24 saat sonrası için tahmin edilen değere göre "
                               "sıralanmıştır. Ayrıntılı grafik ve açıklama için <b>İstasyon "
                               "detayı</b> sekmesine geçin.")
        cards = "".join(
            station_card_html(station_label(service.a.stations[s]),
                              f"{service.a.stations[s]['area_type']} · "
                              f"{service.a.stations[s]['source_type']}",
                              forecasts[s], T) for s in ordered)
        html(f'<div class="hu-grid">{cards}</div>')

        with st.expander("Tablo görünümü"):
            st.dataframe(pd.DataFrame([{
                "İstasyon": station_label(service.a.stations[s]),
                "Şu an (µg/m³)": forecasts[s]["latest_measurement"]["pm25"],
                "24 saat sonra (µg/m³)": forecasts[s]["pm25"],
                "%80'lik aralık, alt sınır": forecasts[s]["interval_80"]["low"],
                "%80'lik aralık, üst sınır": forecasts[s]["interval_80"]["high"],
                "Kategori": forecasts[s]["category"],
                "Uyarı": "Evet" if forecasts[s]["alert"]["is_alert"] else "Hayır",
                "Uyarı riski": "Evet" if forecasts[s]["alert"]["risk"] else "Hayır",
            } for s in ordered]), hide_index=True, width="stretch")
    for s, msg in errors.items():
        html(callout_html("info", f"<b>{station_label(service.a.stations[s])}</b>: {msg}", T))
    html('<p class="hu-lead" style="margin-top:16px"><b>Uyarı:</b> Tahmin, istasyonun karar '
         "eşiğini aşıyor. Eşikler, uyarıların en az %80'ini yakalayacak şekilde ve test dönemi "
         "görülmeden, yalnızca geçmiş veriden seçilmiştir. <b>Uyarı riski:</b> Tahmin eşiğin "
         "altında kalıyor, ancak %80'lik aralığın üst sınırı resmî eşik olan 35,5 µg/m³'ü "
         "aşıyor.</p>")

# --- İstasyon detayı -------------------------------------------------------------------------
with tab_station:
    if not ordered:
        html(callout_html("info", "Şu anda tahmin üretilebilen istasyon yok.", T))
    else:
        slug = st.selectbox("İstasyon seçin", ordered,
                            format_func=lambda x: station_label(service.a.stations[x]))
        f = forecasts[slug]
        a = f["alert"]
        left, right = st.columns([5, 7], gap="large")
        with left:
            if a["is_alert"]:
                status = callout_html("alert", "<b>Uyarı.</b> Tahmin, bu istasyonun karar "
                                               f"eşiğini ({tr_num(a['decision_threshold'])} "
                                               "µg/m³) aşıyor.", T)
            elif a["risk"]:
                status = callout_html("risk", "<b>Uyarı riski.</b> Tahmin eşiğin altında "
                                              "kalıyor, ancak %80'lik aralığın üst sınırı "
                                              "resmî eşiği (35,5 µg/m³) aşıyor.", T)
            else:
                status = callout_html("ok", "<b>Uyarı yok.</b> Tahmin ve %80'lik aralık, "
                                            "uyarı düzeyinin altında.", T)
            lm = f["latest_measurement"]
            measured = (f"Son ölçüm: {tr_num(lm['pm25'])} µg/m³ "
                        f"({tr_datetime(lm['time'], year=False)})"
                        if lm["time"] is not None else "Güncel ölçüm yok")
            low, high = f["interval_80"]["low"], f["interval_80"]["high"]
            chip = category_chip(f["category"], solid=True, t=T, suffix=f" · AQI {f['aqi']}")
            bar = range_html(f["pm25"], low, high, a["decision_threshold"], T)
            advice = callout_html("health", "<b>Ne yapmalı?</b> " + ADVICE[f["category"]], T)
            html(
                '<div class="hu-card" lang="tr">'
                f'<div class="hu-kpi-label">{tr_datetime(f["target_time"])} için tahmin</div>'
                '<div style="display:flex;align-items:baseline;gap:8px;margin-top:10px">'
                f'<span class="hu-hero-value">{tr_num(f["pm25"], 0)}</span>'
                '<span class="hu-unit" style="font-size:1rem">µg/m³</span></div>'
                f'<div class="hu-row">{chip}</div>{bar}'
                f'<div class="hu-meta">%80 olasılıkla <b>{tr_num(low, 0)}–{tr_num(high, 0)} '
                f'µg/m³</b> · {measured}</div>{status}{advice}</div>')
        with right:
            html('<div class="hu-kpi-label" lang="tr" style="margin-bottom:6px">Son 72 saat ve '
                 'önümüzdeki 24 saat</div>')
            st.plotly_chart(forecast_figure(f, T), width="stretch", config=PLOT_CONFIG)
            traj = pd.DataFrame(f["trajectory"]).dropna(subset=["actual"])
            if len(traj) >= 12:
                mae = (traj["pm25"] - traj["actual"]).abs().mean()
                html('<p class="hu-meta">İnce düz çizgi ölçümü, kesikli çizgi aynı saatler için '
                     '24 saat önceden verilmiş tahminleri, kalın çizgi ise önümüzdeki 24 saatin '
                     f'tahminini gösterir. <b>Canlı kontrol:</b> Son {len(traj)} saatteki '
                     f'ortalama hata {tr_num(mae)} µg/m³ (geri testteki 12 aylık ortalama: '
                     '6,8).</p>')

        section("Bu tahmin neden böyle?", explanation_sentence(f["explanation"], markup="html"))
        st.plotly_chart(explanation_figure(f["explanation"], T), width="stretch",
                        config=PLOT_CONFIG)
        base_txt = tr_num(f["explanation"]["base_value"])
        other_txt = tr_num(f["explanation"]["other_features"], sign=True)
        html(f'<p class="hu-meta">Modelin ortalama tahmini: {base_txt} µg/m³. Çubuklar, her '
             'etkenin bu istasyon ve saat için tahmini ne kadar yukarı (↑) ya da aşağı (↓) '
             f'çektiğini gösterir. Diğer özelliklerin toplam katkısı: {other_txt} µg/m³.</p>')

# --- Model performansı -----------------------------------------------------------------------
with tab_model:
    bt = service.a.card.get("backtest_12m", {})
    html('<p class="hu-lead">Son 12 ay (Eylül 2025–Eylül 2026) için ileriye kayan pencereli '
         "(walk-forward) geri test, 8 istasyon. Uyarı eşikleri ve tahmin aralıkları, test "
         "dönemi görülmeden yalnızca geçmiş veriden seçilmiştir.</p>")
    cols = st.columns(4)
    cols[0].markdown(kpi_html("Ortalama hata", tr_num(bt.get("mae", 0), 2),
                              f"µg/m³ (ham CAMS: {tr_num(bt.get('cams_raw_mae', 0), 2)})",
                              "activity"), unsafe_allow_html=True)
    cols[1].markdown(kpi_html("Yakalanan uyarı",
                              tr_pct(bt.get("alert_recall_station_thresholds", 0)),
                              "Gerçek uyarıların oranı (hedef: %80)", "alert"),
                     unsafe_allow_html=True)
    cols[2].markdown(kpi_html("Doğru uyarı oranı",
                              tr_pct(bt.get("alert_precision_station_thresholds", 0)),
                              "Verilen uyarılardan doğru çıkanlar", "shield"),
                     unsafe_allow_html=True)
    cols[3].markdown(kpi_html("Aralık kapsaması",
                              tr_pct(bt.get("interval_80_coverage", 0), 1),
                              "Ölçümlerin %80'lik aralıkta kalma oranı", "eye"),
                     unsafe_allow_html=True)

    curves = load_json("perf_curves.json")
    if curves:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            section("Uyarılarda yakalama ve isabet dengesi",
                    "Eğrideki her nokta farklı bir karar eşiğine karşılık gelir. Model, CAMS'ın "
                    "ve basit yöntemlerin sağ üstünde kalıyor; yani aynı isabet düzeyinde daha "
                    "çok uyarı yakalıyor.")
            op = ({"recall": bt["alert_recall_station_thresholds"],
                   "precision": bt["alert_precision_station_thresholds"]}
                  if "alert_recall_station_thresholds" in bt else None)
            st.plotly_chart(pr_figure(curves, op, T), width="stretch", config=PLOT_CONFIG)
        with c2:
            section("Gerçek değere göre ortalama tahmin",
                    "Çizgi köşegene ne kadar yakınsa tahmin o kadar isabetlidir. Yüksek "
                    "değerler hâlâ düşük tahmin ediliyor (bilinen bir sınırlama); CAMS ise bu "
                    "değerleri çok daha fazla bastırıyor.")
            st.plotly_chart(calibration_figure(curves, T), width="stretch", config=PLOT_CONFIG)
    families = load_json("feature_families.json")
    if families:
        section("Tahmin neye dayanıyor?",
                "Özellik ailelerinin tahmine ortalama katkı payı (TreeSHAP). O gün yayımlanan "
                "hava tahmini, tahminin yaklaşık üçte birini oluşturuyor; CAMS'ın PM2.5 "
                "değerinin payı ise %1'in altında.")
        st.plotly_chart(families_figure(families["family_share_pct"], T), width="stretch",
                        config=PLOT_CONFIG)
    html(f'<p class="hu-meta">Tüm raporlar: <a href="{REPO_URL}/tree/main/reports" '
         'target="_blank" rel="noopener">GitHub · reports</a></p>')

# --- Hakkında --------------------------------------------------------------------------------
with tab_about:
    section("Ne yapıyor?")
    html('<p class="hu-lead">Avrupa\'nın CAMS atmosfer modeli, yaklaşık 11 km çözünürlükte hava '
         "kalitesi tahmini yayımlar; ancak bu tahminlerin Türkiye'deki istasyon ölçümleriyle "
         "uyumu zayıftır (korelasyon: 0,30–0,64). HavaUyarı; CAMS verisini, istasyonun kendi "
         "geçmişini ve o gün yayımlanan hava tahminini birleştirerek her istasyonda <b>24 saat "
         "sonra ölçülecek PM2.5</b> değerini tahmin eder ve gerektiğinde uyarı üretir.</p>")
    section("Veri kaynakları")
    html('<p class="hu-lead">Çevre, Şehircilik ve İklim Değişikliği Bakanlığı Sürekli İzleme '
         "Merkezi (SİM) istasyon ölçümleri (hedef değişken) · Open-Meteo: CAMS kirletici "
         "verileri, bir gün önce yayımlanmış hava tahminleri (Previous Runs) ve meteoroloji "
         "verileri.</p>")
    section("Yöntem")
    html('<p class="hu-lead">LightGBM modeli, 99 özellik. Her istasyonun uyarı eşiği ve %80\'lik '
         "tahmin aralığı, ileriye kayan pencereli (walk-forward) yöntemle yalnızca geçmiş "
         "veriden seçilmiştir. Gelecekteki verinin modele sızmadığı, otomatik testlerle "
         "doğrulanmaktadır.</p>")
    section("Sınırlamalar")
    html('<p class="hu-lead">Ani ve çok yüksek kirlilik olayları hâlâ olduğundan düşük tahmin '
         "ediliyor. Kapsam: 5 şehirde 8 istasyon ve tek tahmin ufku (24 saat). İki Ankara "
         "istasyonunun ölçümlerine duyulan güven düşüktür.</p>")
    html(f'<p class="hu-lead">Kaynak kod ve ayrıntılı raporlar: <a href="{REPO_URL}" '
         f'target="_blank" rel="noopener">{REPO_URL}</a></p>')

html(f'<footer class="hu-footer" lang="tr">{DISCLAIMER}<br>Veri: Çevre, Şehircilik ve İklim '
     "Değişikliği Bakanlığı SİM · Open-Meteo (CAMS, hava tahmini). Harita: © CARTO, "
     "© OpenStreetMap'e katkıda bulunanlar.</footer>")
