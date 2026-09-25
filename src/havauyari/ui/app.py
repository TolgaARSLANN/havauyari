"""HavaUyarı panosu (Faz 6). Tasarım dili: "Parçacık Defteri" (ui/theme.py,
docs/tasarim/parcacik-defteri.md). PM2.5 değeri noktaların yoğunluğuyla gösterilir.

Metinler TDK Yazım Kılavuzu'na göre yazılmıştır: saat biçimi "14.00", ay adları yazıyla,
"%80'lik", "resmî", "tahminî", "olağan dışı" vb.

Gezinme: İstasyon kartındaki düğme, istasyonu seçip "İstasyon detayı" sekmesini açar. Seçili
istasyon adres çubuğunda tutulur (?istasyon=izmir_konak); bu bağlantı doğrudan paylaşılabilir.

Çalıştırma:
    streamlit run src/havauyari/ui/app.py
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pandas as pd
import requests
import streamlit as st

from havauyari.config import ROOT
from havauyari.ops.daily import LOG_PATH, STATUS_PATH, load_log
from havauyari.serving.service import DataUnavailable
from havauyari.ui import state
from havauyari.ui.components import (
    ADVICE,
    CITY_LABELS,
    DISCLAIMER,
    calibration_figure,
    callout_html,
    category_chip,
    category_color,
    explanation_figure,
    explanation_sentence,
    families_figure,
    forecast_figure,
    header_html,
    hero_html,
    hourly_strip_html,
    kpi_html,
    legend_html,
    live_monitor_html,
    mae_bars_html,
    map_figure,
    pipeline_html,
    pr_figure,
    range_html,
    ranking_html,
    skeleton_html,
    station_card_html,
    station_code,
    tr_datetime,
    tr_num,
    tr_pct,
)
from havauyari.ui.theme import EMBER_LINE, card_rules, css, svg, tokens_for

REPORTS = ROOT / "reports"
REPO_URL = "https://github.com/TolgaARSLANN/havauyari"
STALE_AFTER = timedelta(hours=2)
PLOT_CONFIG = {"displaylogo": False, "displayModeBar": False, "locale": "tr"}
# Zaman serisinde yakınlaştırma işe yarar: araç çubuğu yalnızca orada
ZOOM_CONFIG = {**PLOT_CONFIG, "displayModeBar": "hover",
               "modeBarButtonsToRemove": ["select2d", "lasso2d"]}
MAP_CONFIG = {**PLOT_CONFIG, "scrollZoom": False}    # sayfa kaydırması haritaya takılmasın
TABS = ["Genel bakış", "İstasyon detayı", "Model performansı", "Hakkında"]
CARDS_PER_ROW = 4

st.set_page_config(page_title="HavaUyarı · PM2.5 erken uyarı", page_icon=":material/air:",
                   layout="wide", initial_sidebar_state="collapsed")

theme_ctx = getattr(st.context, "theme", None)
T = tokens_for(getattr(theme_ctx, "type", None))
st.markdown(css(T), unsafe_allow_html=True)
# Sayfa dili Türkçe: ekran okuyucular doğru telaffuz eder, CSS büyük harfte i -> İ olur
st.html("<script>(parent.document||document).documentElement.lang='tr';</script>",
        unsafe_allow_javascript=True)


@st.cache_resource(show_spinner=False)
def get_service():
    return state.SERVICE_FACTORY()


def load_forecasts(service) -> tuple[dict, dict]:
    """İstasyonlar paralel çekilir: saatin ilk açılışında süre ağ gecikmesiyle sınırlı kalır.
    (Servisin saatlik önbelleği yarışta bir kaydı kaybederse o istasyon yeniden hesaplanır.)"""

    def one(slug: str):
        try:
            return slug, service.forecast(slug), None
        except DataUnavailable as e:
            return slug, None, str(e)
        except requests.RequestException as e:           # ağ kesintisi: sayfa çökmesin
            name = service.a.stations[slug]["name"]
            return slug, None, (f"{name}: veri kaynağına şu anda ulaşılamıyor "
                                f"({type(e).__name__}); tahmin daha sonra yenilenecek.")

    ok, errors = {}, {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for slug, result, err in pool.map(one, list(service.a.stations)):
            if err is None:
                ok[slug] = result
            else:
                errors[slug] = err
    return ok, errors


def load_json(name: str) -> dict | None:
    path = REPORTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def station_label(s: dict) -> str:
    """İstasyon adı çoğunlukla şehri zaten içeriyor ('İzmir - Konak'). SİM'in kurum eki
    ('-MTHM': Marmara Temiz Hava Merkezi) okura bilgi vermediği için gösterilmez."""
    city = CITY_LABELS.get(s["city"], s["city"])
    name = s["name"].removesuffix("-MTHM").strip()
    return name if name.startswith(city) else f"{city} · {name}"


def section(title: str, lead: str | None = None, fig: str | None = None) -> None:
    """Bölüm: üstte mürekkep çizgisi, solda şekil numarası, serif başlık."""
    fig_html = f'<span class="hu-fig">{fig}</span>' if fig else ""
    st.markdown(f'<div class="hu-section" lang="tr">{fig_html}'
                f'<h2 class="hu-section-title">{title}</h2></div>', unsafe_allow_html=True)
    if lead:
        st.markdown(f'<p class="hu-lead" lang="tr">{lead}</p>', unsafe_allow_html=True)


def html(fragment: str) -> None:
    st.markdown(fragment, unsafe_allow_html=True)


def open_station(slug: str) -> None:
    """Kart düğmesi: istasyonu seç, detay sekmesine geç, adresi güncelle."""
    st.session_state["istasyon"] = slug
    st.session_state["nav"] = TABS[1]
    st.session_state["_scroll_top"] = True
    st.query_params["istasyon"] = slug


def scroll_to_top() -> None:
    """Karttan detaya geçince sayfa başına dön (yoksa kullanıcı sayfanın ortasında kalır)."""
    st.html("<script>(function(){const m=parent.document||document;"
            "for(const el of [m.scrollingElement, m.querySelector('[data-testid=\"stMain\"]'),"
            "m.querySelector('[data-testid=\"stAppViewContainer\"]')]){el&&el.scrollTo&&"
            "el.scrollTo({top:0,behavior:'instant'});}})();</script>",
            unsafe_allow_javascript=True)


def sync_station_param() -> None:
    st.query_params["istasyon"] = st.session_state["istasyon"]


def reading_key() -> str:
    """Şekil 1'in okuma anahtarı: her işaret bir kez, kendi küçük örneğiyle."""
    def glyph(inner: str) -> str:
        return (f'<svg width="34" height="18" viewBox="0 0 34 18" aria-hidden="true" '
                f'style="flex:none">{inner}</svg>')

    dots = "".join(f'<circle cx="{4 + i * 6.5}" cy="{6 + (i % 2) * 6}" r="2.4"/>'
                   for i in range(5))
    items = [
        (glyph(f'<g fill="{category_color("Orta")}">{dots}</g>'),
         "<b>Her nokta bir sayım.</b> Yoğunluk, 24 saat sonrası için tahmini gösterir."),
        (glyph(f'<g fill="{category_color("Orta")}" fill-opacity=".34">{dots}</g>'),
         "<b>Soluk kuyruk:</b> %80'lik aralığın üst kısmı."),
        (glyph(f'<line x1="17" x2="17" y1="1" y2="17" stroke="{T.text}" stroke-width="1.6"/>'),
         "<b>Mürekkep çizgi:</b> tahmin edilen değer."),
        (glyph(f'<line x1="17" x2="17" y1="0" y2="18" stroke="{EMBER_LINE}" '
               f'stroke-width="1.6"/>'),
         "<b>Köz çizgi:</b> resmî uyarı eşiği (35,5 µg/m³). Kuyruğu bu çizgiyi aşan "
         "istasyon için <b>uyarı riski</b> vardır."),
    ]
    rows = "".join(f'<li style="display:flex;gap:14px;align-items:flex-start;padding:12px 0;'
                   f'border-bottom:1px solid var(--hu-border)">{g}<span class="hu-meta" '
                   f'style="font-size:0.9rem">{txt}</span></li>' for g, txt in items)
    return (f'<div lang="tr"><div class="hu-label" style="margin-bottom:6px">Okuma anahtarı'
            f'</div><ul style="list-style:none;margin:0;padding:0">{rows}</ul>'
            f'{legend_html()}</div>')


# --- Veri ------------------------------------------------------------------------------------
header_slot = st.empty()                 # başlık hemen görünür, veri gelince güncellenir
header_slot.markdown(header_html(None, stale=True, t=T), unsafe_allow_html=True)
try:
    service = get_service()
except FileNotFoundError as e:
    st.error(f"Model yüklenemedi: {e}")
    st.stop()

skeleton = st.empty()                    # yükleme sırasında sayfanın iskeleti (düzen kaymaz)
skeleton.markdown(skeleton_html(), unsafe_allow_html=True)
forecasts, errors = load_forecasts(service)
skeleton.empty()

issued = pd.Timestamp(next(iter(forecasts.values()))["issued_at"]) if forecasts else None
latest = [pd.Timestamp(f["latest_measurement"]["time"]) for f in forecasts.values()
          if f["latest_measurement"]["time"] is not None]
stale = issued is None or not latest or (issued - max(latest)) > STALE_AFTER
header_slot.markdown(header_html(issued, stale, T), unsafe_allow_html=True)

ordered = sorted(forecasts, key=lambda s: forecasts[s]["pm25"], reverse=True)
stations = service.a.stations

# Paylaşılan bağlantıyla gelindiyse (?istasyon=...) istasyonu seç ve detay sekmesini aç
if ordered and "istasyon" not in st.session_state:
    wanted = st.query_params.get("istasyon")
    st.session_state["istasyon"] = wanted if wanted in ordered else ordered[0]
    if wanted in ordered:
        st.session_state["nav"] = TABS[1]

tab_overview, tab_station, tab_model, tab_about = st.tabs(TABS, key="nav", on_change="rerun")

# --- Genel bakış -----------------------------------------------------------------------------
with tab_overview:
    if not forecasts:
        html(callout_html("info", "Şu anda tahmin üretilebilen istasyon yok.", T))
    else:
        rows = [{"slug": s, "name": station_label(stations[s]),
                 "lat": stations[s]["lat"], "lon": stations[s]["lon"],
                 "pm25": forecasts[s]["pm25"], "category": forecasts[s]["category"],
                 "low": forecasts[s]["interval_80"]["low"],
                 "high": forecasts[s]["interval_80"]["high"],
                 "is_alert": forecasts[s]["alert"]["is_alert"],
                 "risk": forecasts[s]["alert"]["risk"]} for s in ordered]
        html(hero_html(rows, forecasts[ordered[0]]["target_time"], T))

        section("Parçacık yoğunluğu", "Sekiz istasyon, aynı ölçekte. Noktaların yoğunluğu "
                                      "24 saat sonrası için tahmini, soluk kuyruk %80'lik "
                                      "aralığı gösterir.", fig="Şekil 1")
        html(ranking_html(rows, T))

        section("Harita", fig="Şekil 2")
        left, right = st.columns([7, 5], gap="large")
        with left:
            # SVG harita en-boy oranını korur: geniş ve dar ekran için iki yükseklik üretilir,
            # CSS ekran genişliğine göre birini gösterir (dar ekranda üstte-altta boşluk kalmaz)
            with st.container(key="map-wide"):
                st.plotly_chart(map_figure(rows, T), width="stretch", config=MAP_CONFIG)
            with st.container(key="map-narrow"):
                st.plotly_chart(map_figure(rows, T, height=260), width="stretch",
                                config=MAP_CONFIG)
        with right:
            html(reading_key())

        section("İstasyonlar", "Her kartta son 48 saatin ölçümü (mürekkep) ve önümüzdeki "
                               "24 saatin tahmini (çivit). Ayrıntılar için karta dokunun.",
                fig="Şekil 3")
        html(card_rules({f"card-{s}": category_color(forecasts[s]["category"])
                         for s in ordered}))
        for i in range(0, len(ordered), CARDS_PER_ROW):
            cols = st.columns(CARDS_PER_ROW)
            for col, s in zip(cols, ordered[i:i + CARDS_PER_ROW], strict=False):
                with col.container(key=f"card-{s}"):
                    html(station_card_html(
                        station_label(stations[s]),
                        f"{stations[s]['area_type']} · {stations[s]['source_type']}",
                        forecasts[s], T))
                    st.button("Ayrıntılar", key=f"go-{s}", on_click=open_station, args=(s,),
                              icon=":material/arrow_forward:", icon_position="right",
                              type="tertiary", width="stretch")

        st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
        with st.expander("Tablo görünümü", icon=":material/table:"):
            st.dataframe(pd.DataFrame([{
                "İstasyon": station_label(stations[s]),
                "Şu an (µg/m³)": forecasts[s]["latest_measurement"]["pm25"],
                "24 saat sonra (µg/m³)": forecasts[s]["pm25"],
                "%80'lik aralık, alt sınır": forecasts[s]["interval_80"]["low"],
                "%80'lik aralık, üst sınır": forecasts[s]["interval_80"]["high"],
                "Kategori": forecasts[s]["category"],
                "Uyarı": "Evet" if forecasts[s]["alert"]["is_alert"] else "Hayır",
                "Uyarı riski": "Evet" if forecasts[s]["alert"]["risk"] else "Hayır",
            } for s in ordered]), hide_index=True, width="stretch")
        with st.expander("Uyarı ve uyarı riski nasıl belirleniyor?", icon=":material/help:"):
            html('<p class="hu-prose" lang="tr"><b>Uyarı:</b> Tahmin, istasyonun karar eşiğini '
                 "aşıyor. Eşikler, uyarıların en az %80'ini yakalayacak şekilde ve test dönemi "
                 "görülmeden, yalnızca geçmiş veriden seçilmiştir (18,5–32 µg/m³).<br>"
                 "<b>Uyarı riski:</b> Tahmin eşiğin altında kalıyor, ancak %80'lik aralığın üst "
                 "sınırı resmî eşik olan 35,5 µg/m³'ü aşıyor.</p>")
    for s, msg in errors.items():
        html(callout_html("info", f"<b>{station_label(stations[s])}</b>: {msg}", T))

# --- İstasyon detayı -------------------------------------------------------------------------
with tab_station:
    if not ordered:
        html(callout_html("info", "Şu anda tahmin üretilebilen istasyon yok.", T))
    else:
        if st.session_state.pop("_scroll_top", False):
            scroll_to_top()
        slug = st.pills("İstasyon seçin", ordered, key="istasyon", required=True,
                        format_func=lambda x: station_label(stations[x]),
                        on_change=sync_station_param, label_visibility="collapsed")
        slug = slug or ordered[0]
        f = forecasts[slug]
        a = f["alert"]
        name = station_label(stations[slug])
        st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
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
            measured = (f"Son ölçüm <b>{tr_num(lm['pm25'])} µg/m³</b> "
                        f"({tr_datetime(lm['time'], year=False)})"
                        if lm["time"] is not None else "Güncel ölçüm yok")
            low, high = f["interval_80"]["low"], f["interval_80"]["high"]
            chip = category_chip(f["category"], solid=True, t=T, suffix=f" · AQI {f['aqi']}")
            bar = range_html(f["pm25"], low, high, a["decision_threshold"], T)
            advice = callout_html("health", "<b>Ne yapmalı?</b> " + ADVICE[f["category"]], T)
            html(
                '<div class="hu-forecast" lang="tr">'
                f'<div class="hu-eyebrow">{svg("pin", 13)}<b>{station_code(name)}</b> · '
                f'{tr_datetime(f["target_time"])} için tahmin</div>'
                f'<div class="hu-hero-value"><span class="hu-num">{tr_num(f["pm25"], 0)}</span>'
                '<small>µg/m³</small></div>'
                f'<div class="hu-forecast-meta">{chip}</div>{bar}'
                f'<div class="hu-meta">%80 olasılıkla <b>{tr_num(low, 0)}–{tr_num(high, 0)} '
                f'µg/m³</b> · {measured}</div>{status}{advice}</div>')
        with right:
            html(f'<div class="hu-panel" lang="tr"><div class="hu-label" '
                 f'style="margin-bottom:10px">Önümüzdeki 24 saat · saat saat</div>'
                 f'{hourly_strip_html(f, T)}</div>')
            html('<div class="hu-label" lang="tr" style="margin:22px 0 4px">Son 72 saat ve '
                 'önümüzdeki 24 saat</div>')
            st.plotly_chart(forecast_figure(f, T), width="stretch", config=ZOOM_CONFIG)
            traj = pd.DataFrame(f["trajectory"]).dropna(subset=["actual"])
            if len(traj) >= 12:
                mae = (traj["pm25"] - traj["actual"]).abs().mean()
                html('<p class="hu-meta" lang="tr">Mürekkep çizgi ölçümü, noktalı çizgi aynı '
                     'saatler için 24 saat önceden verilmiş tahminleri, kalın çivit çizgi '
                     'önümüzdeki 24 saatin tahminini gösterir. <b>Canlı kontrol:</b> Son '
                     f'{len(traj)} saatteki ortalama hata {tr_num(mae)} µg/m³ (geri testteki '
                     '12 aylık ortalama: 6,8).</p>')

        section("Bu tahmin neden böyle?", fig="Açıklama")
        e_left, e_right = st.columns([5, 7], gap="large")
        with e_left:
            base_txt = tr_num(f["explanation"]["base_value"])
            other_txt = tr_num(f["explanation"]["other_features"], sign=True)
            html(callout_html("info", explanation_sentence(f["explanation"], markup="html"), T)
                 + f'<p class="hu-meta" lang="tr" style="margin-top:14px">Model, ortalama bir '
                 f'gün için {base_txt} µg/m³ tahmin eder. Çubuklar, en etkili beş etkenin bu '
                 'istasyon ve saat için tahmini ne kadar yukarı (↑, pas) ya da aşağı (↓, '
                 f'çivit) çektiğini gösterir. Diğer özelliklerin toplam katkısı: {other_txt} '
                 'µg/m³.</p>')
        with e_right:
            st.plotly_chart(explanation_figure(f["explanation"], T), width="stretch",
                            config=PLOT_CONFIG)

# --- Model performansı -----------------------------------------------------------------------
with tab_model:
    bt = service.a.card.get("backtest_12m", {})
    mae, cams = bt.get("mae", 0), bt.get("cams_raw_mae", 0)
    gain = 1 - mae / cams if cams else 0
    left, right = st.columns([5, 7], gap="large")
    with left:
        html('<div class="hu-forecast" lang="tr">'
             f'<div class="hu-eyebrow">{svg("trending_down", 13)}12 aylık geri test · '
             '8 istasyon</div>'
             f'<div class="hu-big" style="margin-top:22px">{tr_pct(gain)}</div>'
             '<div class="hu-big-sub">daha az hata</div>'
             '<p class="hu-lead" style="margin-top:16px">Avrupa\'nın CAMS modeline göre '
             f'ortalama mutlak hata <b>{tr_num(cams, 2)}</b> µg/m³\'ten <b>{tr_num(mae, 2)}'
             '</b> µg/m³\'e iniyor. Eşikler ve aralıklar, test dönemi görülmeden yalnızca '
             'geçmiş veriden seçildi.</p></div>')
    with right:
        html('<div lang="tr"><div class="hu-label" style="margin-bottom:6px">Ortalama hata · '
             '<span class="hu-u">µg/m³</span> · kısa sıra daha iyi</div>'
             f'{mae_bars_html(T)}</div>')

    html('<div class="hu-kpis">'
         + kpi_html("Ortalama hata", tr_num(mae, 2),
                    f"µg/m³ (ham CAMS: {tr_num(cams, 2)})", "activity")
         + kpi_html("Yakalanan uyarı", tr_pct(bt.get("alert_recall_station_thresholds", 0)),
                    "Gerçek uyarıların oranı (hedef: %80)", "target")
         + kpi_html("Doğru uyarı oranı",
                    tr_pct(bt.get("alert_precision_station_thresholds", 0)),
                    "Verilen uyarılardan doğru çıkanlar", "shield")
         + kpi_html("Aralık kapsaması", tr_pct(bt.get("interval_80_coverage", 0), 1),
                    "Ölçümlerin %80'lik aralıkta kalma oranı", "eye")
         + "</div>")

    section("Canlı izleme", "Günlük tahmin işi her sabah tüm istasyonlar için tahmin üretir; "
                            "ertesi gün her tahmin gerçekleşen ölçümle karşılaştırılır. Canlı "
                            "hata geri testin 1,5 katını aşarsa sapma işaretlenir.",
            fig="İzleme")
    live_status = (json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                   if STATUS_PATH.exists() else None)
    html(live_monitor_html(load_log(LOG_PATH), live_status, T))

    curves = load_json("perf_curves.json")
    if curves:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            section("Yakalama ve isabet",
                    "Eğrideki her nokta farklı bir karar eşiğine karşılık gelir. Model, CAMS'ın "
                    "ve basit yöntemlerin sağ üstünde kalıyor; yani aynı isabet düzeyinde daha "
                    "çok uyarı yakalıyor.", fig="Şekil 4")
            op = ({"recall": bt["alert_recall_station_thresholds"],
                   "precision": bt["alert_precision_station_thresholds"]}
                  if "alert_recall_station_thresholds" in bt else None)
            st.plotly_chart(pr_figure(curves, op, T), width="stretch", config=PLOT_CONFIG)
        with c2:
            section("Kalibrasyon",
                    "Çizgi köşegene ne kadar yakınsa tahmin o kadar isabetlidir. Yüksek "
                    "değerler hâlâ düşük tahmin ediliyor (bilinen bir sınırlama); CAMS ise bu "
                    "değerleri çok daha fazla bastırıyor.", fig="Şekil 5")
            st.plotly_chart(calibration_figure(curves, T), width="stretch", config=PLOT_CONFIG)
    families = load_json("feature_families.json")
    if families:
        section("Tahmin neye dayanıyor?",
                "Özellik ailelerinin tahmine ortalama katkı payı (TreeSHAP). O gün yayımlanan "
                "hava tahmini, tahminin yaklaşık üçte birini oluşturuyor; CAMS'ın PM2.5 "
                "değerinin payı ise %1'in altında.", fig="Şekil 6")
        st.plotly_chart(families_figure(families["family_share_pct"], T), width="stretch",
                        config=PLOT_CONFIG)
    html(f'<p class="hu-meta">Tüm raporlar: <a href="{REPO_URL}/tree/main/reports" '
         'target="_blank" rel="noopener">GitHub · reports</a></p>')

# --- Hakkında --------------------------------------------------------------------------------
with tab_about:
    section("Nasıl çalışır?", "Her saat yeni ölçümler ve hava tahmini alınır, her istasyon için "
                              "24 saat sonrasının PM2.5 değeri hesaplanır.", fig="Akış")
    html(pipeline_html())
    c1, c2 = st.columns(2, gap="large")
    with c1:
        section("Ne yapıyor?")
        html('<p class="hu-prose" lang="tr">Avrupa\'nın CAMS atmosfer modeli, yaklaşık 11 km '
             "çözünürlükte hava kalitesi tahmini yayımlar; ancak bu tahminlerin Türkiye'deki "
             "istasyon ölçümleriyle uyumu zayıftır (korelasyon: 0,30–0,64). HavaUyarı; CAMS "
             "verisini, istasyonun kendi geçmişini ve o gün yayımlanan hava tahminini "
             "birleştirerek her istasyonda <b>24 saat sonra ölçülecek PM2.5</b> değerini "
             "tahmin eder ve gerektiğinde uyarı üretir.</p>")
        section("Veri kaynakları")
        html('<p class="hu-prose" lang="tr">Çevre, Şehircilik ve İklim Değişikliği Bakanlığı '
             "Sürekli İzleme Merkezi (SİM) istasyon ölçümleri (hedef değişken) · Open-Meteo: "
             "CAMS kirletici verileri, bir gün önce yayımlanmış hava tahminleri (Previous Runs) "
             "ve meteoroloji verileri.</p>")
    with c2:
        section("Yöntem")
        html('<p class="hu-prose" lang="tr">LightGBM modeli, 99 özellik. Her istasyonun uyarı '
             "eşiği ve %80'lik tahmin aralığı, ileriye kayan pencereli (walk-forward) yöntemle "
             "yalnızca geçmiş veriden seçilmiştir. Gelecekteki verinin modele sızmadığı, "
             "otomatik testlerle doğrulanmaktadır.</p>")
        section("Sınırlamalar")
        html('<p class="hu-prose" lang="tr">Ani ve çok yüksek kirlilik olayları hâlâ olduğundan '
             "düşük tahmin ediliyor. Kapsam: 5 şehirde 8 istasyon ve tek tahmin ufku (24 saat). "
             "İki Ankara istasyonunun ölçümlerine duyulan güven düşüktür.</p>")
    html(f'<p class="hu-prose" lang="tr" style="margin-top:18px">Kaynak kod ve ayrıntılı '
         f'raporlar: <a href="{REPO_URL}" target="_blank" rel="noopener">{REPO_URL} '
         f'{svg("external", 13)}</a></p>')

html(f'<footer class="hu-footer" lang="tr"><div>{DISCLAIMER}<br>Veri: Çevre, Şehircilik ve '
     "İklim Değişikliği Bakanlığı SİM · Open-Meteo (CAMS, hava tahmini). Harita: © CARTO, "
     "© OpenStreetMap'e katkıda bulunanlar.</div>"
     '<div class="hu-mono">HavaUyarı · Parçacık Defteri<br>PM2.5 · <span class="hu-u">µg/m³'
     '</span> · t + 24</div>'
     "</footer>")
