"""Panonun saf (Streamlit'ten bağımsız, test edilebilir) parçaları: metinler, HTML kartları,
Plotly grafikleri. Görsel kararlar ui/theme.py'deki tasarım sisteminden gelir."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.graph_objects as go

from havauyari.alerts.aqi import CATEGORIES, PM25_BREAKPOINTS
from havauyari.ui.theme import LIGHT, Tokens, plotly_layout, svg

OFFICIAL_ALERT = 35.5

# US EPA AQI renkleri. Metin rengi kontrastı ≥ 4.5:1 olacak şekilde seçildi
# (#FF0000 üzerinde beyaz 4.0:1 kaldığı için "Sağlıksız" siyah metin kullanır).
CATEGORY_COLORS = {
    "İyi": "#00e400",
    "Orta": "#ffff00",
    "Hassas gruplar için sağlıksız": "#ff7e00",
    "Sağlıksız": "#ff0000",
    "Çok sağlıksız": "#8f3f97",
    "Tehlikeli": "#7e0023",
}
CATEGORY_TEXT_COLORS = {c: ("#ffffff" if c in ("Çok sağlıksız", "Tehlikeli") else "#000000")
                        for c in CATEGORIES}
CATEGORY_SHORT = {"Hassas gruplar için sağlıksız": "Hassas gruplar"}

# Genel bilgilendirme (US EPA AQI rehberinden özetlenmiştir; tıbbi tavsiye değildir).
# Yazım: TDK Yazım Kılavuzu (olağan dışı, mekân, resmî, tahminî).
ADVICE = {
    "İyi": "Hava kalitesi iyi. Açık havadaki etkinlikler için uygun bir gün.",
    "Orta": "Hava kalitesi kabul edilebilir düzeyde. Kirliliğe olağan dışı duyarlı kişiler, "
            "açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmayı düşünebilir.",
    "Hassas gruplar için sağlıksız": "Astım, kalp ya da akciğer hastalığı olanlar, yaşlılar "
            "ve çocuklar açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmalıdır.",
    "Sağlıksız": "Herkes açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmalıdır; "
            "hassas gruplar bu tür etkinliklerden kaçınmalıdır.",
    "Çok sağlıksız": "Herkes açık havada fiziksel etkinlikten kaçınmalıdır; hassas gruplar "
            "mümkünse kapalı alanda kalmalıdır.",
    "Tehlikeli": "Herkes açık havadaki etkinliklerden kaçınmalı ve mümkünse kapalı alanda "
            "kalmalıdır.",
}
DISCLAIMER = ("Bu tahminler bir makine öğrenmesi modeli tarafından üretilir ve yalnızca "
              "bilgilendirme amaçlıdır; resmî hava kalitesi uyarılarının ve tıbbi tavsiyenin "
              "yerine geçmez.")

TR_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
             "Eylül", "Ekim", "Kasım", "Aralık"]

CITY_LABELS = {"istanbul": "İstanbul", "ankara": "Ankara", "izmir": "İzmir", "bursa": "Bursa",
               "kocaeli": "Kocaeli"}

# Sık görülen özelliklerin okunur adları
FEATURE_LABELS = {
    "station_pm25": "istasyonun şu anki ölçümü",
    "station_pm25_lag1": "bir saat önceki ölçüm",
    "station_pm25_lag2": "iki saat önceki ölçüm",
    "station_pm25_lag3": "üç saat önceki ölçüm",
    "station_pm25_lag24": "24 saat önceki ölçüm",
    "station_pm25_lag168": "bir hafta önceki ölçüm",
    "station_pm25_tgt_day_ago": "hedef saatin bir gün önceki ölçümü",
    "station_pm25_tgt_week_ago": "hedef saatin bir hafta önceki ölçümü",
    "station_pm25_rollmean24": "son 24 saatin ortalaması",
    "station_pm25_rollmean168": "son bir haftanın ortalaması",
    "station_pm25_rollmax24": "son 24 saatin en yüksek değeri",
    "station_pm25_rollstd168": "son bir haftadaki dalgalanma",
    "station_pm10": "istasyonun PM10 ölçümü",
    "fc_win_wind_mean": "önümüzdeki 24 saatin tahminî ortalama rüzgârı",
    "fc_win_wind_min": "önümüzdeki 24 saatin tahminî en zayıf rüzgârı",
    "fc_win_calm_hours": "önümüzdeki 24 saatteki tahminî durgun saat sayısı",
    "fc_win_precip_sum": "önümüzdeki 24 saatin tahminî yağışı",
    "fc_win_temp_range": "önümüzdeki 24 saatin tahminî sıcaklık farkı",
    "fc_win_temp_min": "önümüzdeki 24 saatin tahminî en düşük sıcaklığı",
    "fc_win_cloud_mean": "önümüzdeki 24 saatin tahminî bulutluluğu",
    "fc_tgt_humidity": "hedef saatteki tahminî nem",
    "fc_tgt_wind_speed": "hedef saatteki tahminî rüzgâr hızı",
    "fc_tgt_wind_u": "hedef saatteki tahminî rüzgâr yönü (doğu-batı)",
    "fc_tgt_wind_v": "hedef saatteki tahminî rüzgâr yönü (kuzey-güney)",
    "fc_tgt_temperature": "hedef saatteki tahminî sıcaklık",
    "fc_tgt_temp_change": "tahminî sıcaklık değişimi",
    "fc_tgt_pressure_change": "tahminî basınç değişimi",
    "fc_tgt_cloud_cover": "hedef saatteki tahminî bulutluluk",
    "surface_pressure": "şu anki hava basıncı",
    "heating_degree_rollmean24": "son 24 saatteki ısınma ihtiyacı",
    "calm_hours24": "son 24 saatteki durgun saat sayısı",
    "wind_speed_rollmean24": "son 24 saatin ortalama rüzgârı",
    "hour_sin": "günün saati", "hour_cos": "günün saati",
    "tgt_hour_sin": "hedef saat", "tgt_hour_cos": "hedef saat",
    "month_sin": "mevsim", "month_cos": "mevsim",
    "dayofweek": "haftanın günü", "tgt_dayofweek": "hedef günün haftanın hangi günü olduğu",
    "station_code": "istasyonun kendine özgü seviyesi",
    "city_code": "şehrin kendine özgü seviyesi",
}

MODEL_LABELS = {"lgbm_gercekci": "HavaUyarı", "lgbm_iyimser": "HavaUyarı (üst sınır)",
                "persistence": "Yarın da bugün gibi", "cams_raw": "Ham CAMS",
                "cams_scaled": "Ölçeklenmiş CAMS"}


# ---------------------------------------------------------------------------------------------
# Metin yardımcıları
# ---------------------------------------------------------------------------------------------
def feature_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name)


def tr_num(x: float, digits: int = 1, sign: bool = False) -> str:
    """Türkçe ondalık biçimi: 6.78 -> '6,78'; sign=True: '+0,9' / '−2,8'."""
    s = f"{abs(x):.{digits}f}".replace(".", ",")
    if sign:
        return ("+" if x > 0 else "−" if x < 0 else "") + s
    return ("−" if x < 0 else "") + s


def tr_datetime(ts, year: bool = True) -> str:
    """TDK'ye uygun tarih-saat: '24 Eylül 2026, 14.00' (saat ile dakika arasında nokta)."""
    ts = pd.Timestamp(ts)
    y = f" {ts.year}" if year else ""
    return f"{ts.day} {TR_MONTHS[ts.month - 1]}{y}, {ts:%H.%M}"


def tr_short(ts) -> str:
    """Kısa biçim (kartlar için): '24.09, 14.00'."""
    return f"{pd.Timestamp(ts):%d.%m, %H.%M}"


def tr_pct(x: float, digits: int = 0) -> str:
    """Türkçede yüzde işareti sayıdan önce gelir: 0.824 -> '%82' (digits=1: '%82,4')."""
    return "%" + tr_num(x * 100, digits)


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#cccccc")


def explanation_sentence(explanation: dict, markup: str = "md") -> str:
    """Katkılardan sade Türkçe özet cümle. markup: "md" (**kalın**) ya da "html" (<b>)."""

    def bold(s: str) -> str:
        return f"<b>{escape(s)}</b>" if markup == "html" else f"**{s}**"

    feats = explanation["top_features"]
    up = [f for f in feats if f["contribution"] > 0]
    down = [f for f in feats if f["contribution"] < 0]
    parts = []
    if up:
        top = max(up, key=lambda f: f["contribution"])
        parts.append(f"Tahmini en çok {bold(feature_label(top['feature']))} yükseltiyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if down:
        top = min(down, key=lambda f: f["contribution"])
        parts.append(f"en çok {bold(feature_label(top['feature']))} düşürüyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if not parts:
        return "Belirgin bir etken yok; tahmin, ortalamaya yakın."
    sentence = "; ".join(parts) + "."
    return sentence[0].upper() + sentence[1:]


# ---------------------------------------------------------------------------------------------
# HTML parçaları (renk her zaman metin ve/veya ikonla birlikte)
# ---------------------------------------------------------------------------------------------
def header_html(issued: pd.Timestamp | None, stale: bool, t: Tokens = LIGHT) -> str:
    if issued is None:
        status = (f'<span class="hu-dot" style="background:{t.muted}"></span>'
                  "Veri bekleniyor")
    else:
        color, label = (t.warn, "Veri gecikmeli") if stale else (t.ok, "Canlı")
        status = (f'<span class="hu-dot" style="background:{color}"></span>'
                  f"<strong style='color:{color}'>{label}</strong> · "
                  f"Son güncelleme: {tr_datetime(issued)}")
    # lang="tr": CSS ile büyük harfe çevrilen metinlerde i → İ dönüşümü doğru yapılır
    return (f'<header class="hu-header" lang="tr"><div class="hu-brand">'
            f'<div class="hu-logo">{svg("wind", 24, "#ffffff")}</div><div>'
            f'<h1 class="hu-title">HavaUyarı</h1>'
            f'<p class="hu-subtitle">Türkiye\'deki hava kalitesi istasyonlarında 24 saat sonra '
            f'ölçülecek PM2.5 değeri için tahmin ve erken uyarı</p></div></div>'
            f'<div class="hu-status" role="status">{svg("clock", 16)}{status}</div></header>')


def kpi_html(label: str, value: str, sub: str = "", icon: str | None = None) -> str:
    ic = svg(icon, 14) if icon else ""
    sub_html = f'<div class="hu-kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="hu-card hu-kpi" lang="tr"><div class="hu-kpi-label">{ic}'
            f'{escape(label)}</div><div class="hu-kpi-value">{value}</div>{sub_html}</div>')


def category_chip(category: str, solid: bool = False, t: Tokens = LIGHT,
                  suffix: str = "") -> str:
    label = escape(CATEGORY_SHORT.get(category, category) + suffix)
    if solid:
        return (f'<span class="hu-chip" style="background:{category_color(category)};'
                f'color:{CATEGORY_TEXT_COLORS.get(category, "#000")}">{label}</span>')
    return (f'<span class="hu-chip" style="background:{t.surface_alt};color:{t.text}" '
            f'title="{escape(category)}"><span class="hu-chip-swatch" '
            f'style="background:{category_color(category)}"></span>{label}</span>')


def flags_html(is_alert: bool, risk: bool, t: Tokens = LIGHT) -> str:
    if is_alert:
        return f'<span class="hu-flag" style="color:{t.danger}">{svg("alert", 14)}Uyarı</span>'
    if risk:
        return (f'<span class="hu-flag" style="color:{t.warn}">{svg("eye", 14)}'
                "Uyarı riski</span>")
    return f'<span class="hu-flag" style="color:{t.ok}">{svg("shield", 14)}Uyarı yok</span>'


def station_card_html(name: str, subtitle: str, f: dict, t: Tokens = LIGHT) -> str:
    """subtitle: istasyon türü (örn. 'Kentsel · Trafik'); ad zaten şehri içerir."""
    lm = f["latest_measurement"]
    now_txt = (f"şu an {tr_num(lm['pm25'])}" if lm["pm25"] is not None
               else "güncel ölçüm yok")
    return (
        f'<article class="hu-card hu-station" lang="tr" aria-label="{escape(name)}">'
        f'<div class="hu-station-head"><div><div class="hu-station-name">{escape(name)}</div>'
        f'<div class="hu-station-city">{svg("pin", 12)}{escape(subtitle)}</div></div>'
        f'{flags_html(f["alert"]["is_alert"], f["alert"]["risk"], t)}</div>'
        f'<div class="hu-station-value">{tr_num(f["pm25"], 0)}<span class="hu-unit">µg/m³'
        f'</span></div>'
        f'<div class="hu-row">{category_chip(f["category"], t=t)}'
        f'<span class="hu-meta" title="%80 olasılıkla bu aralıkta">'
        f'{tr_num(f["interval_80"]["low"], 0)}–{tr_num(f["interval_80"]["high"], 0)} (%80) · '
        f'{now_txt}</span></div></article>')


def legend_html() -> str:
    """Kategoriler ve PM2.5 aralıkları (µg/m³): 'Orta (9,1–35,4)', 'Sağlıksız (55,5 ve üzeri)'."""
    items = []
    for i, (lo, hi, _a, _b, c) in enumerate(PM25_BREAKPOINTS[:4]):
        rng = (f"{tr_num(lo, 1)} ve üzeri" if i == 3 else f"{tr_num(lo, 1)}–{tr_num(hi, 1)}")
        items.append(f'<span><span class="hu-chip-swatch" '
                     f'style="background:{category_color(c)}"></span>{escape(c)} ({rng})</span>')
    return (f'<div class="hu-legend" aria-label="Hava kalitesi kategorileri ve PM2.5 aralıkları '
            f'(µg/m³)"><span><b>PM2.5 (µg/m³):</b></span>{"".join(items)}</div>')


def range_html(pred: float, low: float, high: float, decision: float,
               t: Tokens = LIGHT) -> str:
    """%80 aralığı, tahmini ve resmî uyarı eşiğini aynı ölçekte gösteren yatay çubuk."""
    top = max(60.0, high * 1.15, OFFICIAL_ALERT * 1.25)

    def pct(v: float) -> float:
        return max(0.0, min(100.0, v / top * 100))

    ticks = "".join(f'<span class="hu-range-axis" style="left:{pct(v):.1f}%">{v:g}</span>'
                    for v in range(0, int(top) + 1, 20))
    return (
        f'<div class="hu-range" role="img" aria-label="Tahmin: {tr_num(pred)} µg/m³. %80 '
        f'olasılıkla {tr_num(low)} ile {tr_num(high)} arasında. Resmî uyarı eşiği: 35,5 µg/m³.">'
        f'<div class="hu-range-band" style="left:{pct(low):.1f}%;'
        f'width:{pct(high) - pct(low):.1f}%"></div>'
        f'<div class="hu-range-point" style="left:{pct(pred):.1f}%"></div>'
        f'<div class="hu-range-thr" style="left:{pct(OFFICIAL_ALERT):.1f}%"></div>'
        f'<span class="hu-range-label" style="left:{pct(OFFICIAL_ALERT):.1f}%">'
        f'resmî eşik 35,5</span>'
        f'{ticks}</div>')


def callout_html(kind: str, text: str, t: Tokens = LIGHT) -> str:
    color, icon = {"alert": (t.danger, "alert"), "risk": (t.warn, "eye"),
                   "ok": (t.ok, "shield"), "info": (t.data, "info"),
                   "health": (t.muted, "heart")}[kind]
    return (f'<div class="hu-callout" lang="tr" style="border-color:{color};color:{t.text}">'
            f'<span style="color:{color};margin-top:2px">{svg(icon, 18)}</span>'
            f'<div>{text}</div></div>')


# ---------------------------------------------------------------------------------------------
# Grafikler
# ---------------------------------------------------------------------------------------------
def _aqi_bands(fig: go.Figure, y_max: float) -> None:
    for c_lo, c_hi, _i_lo, _i_hi, name in PM25_BREAKPOINTS:
        if c_lo > y_max:
            break
        fig.add_hrect(y0=c_lo, y1=min(c_hi + 0.1, y_max), fillcolor=category_color(name),
                      opacity=0.07, line_width=0, layer="below")


def forecast_figure(forecast: dict, t: Tokens = LIGHT) -> go.Figure:
    """Son 72 saatin ölçümü (düz) + aynı saatler için 24 saat önceden verilmiş tahminler
    (kesikli) + önümüzdeki 24 saatin tahmini (kalın) ve %80'lik aralık."""
    hist = pd.DataFrame(forecast["history"])
    traj = pd.DataFrame(forecast["trajectory"])
    now = pd.Timestamp(forecast["issued_at"])
    fig = go.Figure()
    hover = "%{x|%d.%m, %H.%M}<br>%{y:.1f} µg/m³<extra>%{fullData.name}</extra>"
    if not traj.empty:
        traj["target_time"] = pd.to_datetime(traj["target_time"])
        past = traj[traj["target_time"] <= now]
        future = traj[traj["target_time"] > now]
        fig.add_trace(go.Scatter(
            x=list(future["target_time"]) + list(future["target_time"][::-1]),
            y=list(future["high"]) + list(future["low"][::-1]), fill="toself",
            fillcolor=t.data_soft, line={"width": 0}, hoverinfo="skip",
            name="%80'lik aralık"))
        fig.add_trace(go.Scatter(x=past["target_time"], y=past["pm25"], mode="lines",
                                 line={"color": t.data, "dash": "dash", "width": 1.6},
                                 name="önceki tahminler", hovertemplate=hover))
        fig.add_trace(go.Scatter(x=future["target_time"], y=future["pm25"], mode="lines",
                                 line={"color": t.data, "width": 3.2},
                                 name="tahmin", hovertemplate=hover))
    if not hist.empty:
        hist["time"] = pd.to_datetime(hist["time"])
        fig.add_trace(go.Scatter(x=hist["time"], y=hist["pm25"], mode="lines",
                                 line={"color": t.measured, "width": 2}, name="ölçüm",
                                 hovertemplate=hover))
    y_values = pd.concat([hist.get("pm25", pd.Series(dtype=float)),
                          traj.get("high", pd.Series(dtype=float))]).dropna()
    y_max = max(50.0, float(y_values.max()) * 1.12 if len(y_values) else 50.0)
    _aqi_bands(fig, y_max)
    fig.add_hline(y=OFFICIAL_ALERT, line={"color": "#FF7E00", "dash": "dot", "width": 1.5},
                  annotation_text="resmî uyarı eşiği (35,5)", annotation_position="top left",
                  annotation_font={"color": t.muted, "size": 11})
    fig.add_vline(x=now, line={"color": t.muted, "width": 1})
    fig.add_annotation(x=now, y=y_max, text="şimdi", showarrow=False, yanchor="bottom",
                       font={"color": t.muted, "size": 11})
    fig.update_layout(**plotly_layout(
        t, height=400, hovermode="x unified",
        yaxis={"title": {"text": "PM2.5 (µg/m³)"}, "range": [0, y_max * 1.06]},
        xaxis={"tickformat": "%d.%m\n%H.%M"},
        legend={"orientation": "h", "y": -0.16, "x": 0},
        margin={"l": 8, "r": 8, "t": 24, "b": 8}))
    return fig


def explanation_figure(explanation: dict, t: Tokens = LIGHT) -> go.Figure:
    """Katkılar: artıran turuncu, azaltan mavi (renk körlüğüne uygun) + işaretli değer etiketi."""
    feats = explanation["top_features"][::-1]
    labels = [feature_label(f["feature"]) for f in feats]
    values = [f["contribution"] for f in feats]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=[t.increase if v > 0 else t.decrease for v in values],
        text=[f"{tr_num(v, sign=True)} {'↑' if v > 0 else '↓'}" for v in values],
        textposition="outside", textfont={"color": t.text},
        hovertemplate="%{y}: %{x:+.2f} µg/m³<extra></extra>"))
    fig.add_vline(x=0, line={"color": t.muted, "width": 1})
    span = max(abs(v) for v in values) if values else 1
    fig.update_layout(**plotly_layout(
        t, height=280, showlegend=False,
        xaxis={"title": {"text": "tahmine katkı (µg/m³)", "font": {"color": t.muted}},
               "range": [-span * 1.35, span * 1.35]},
        yaxis={"tickfont": {"color": t.text}}))
    return fig


def map_figure(rows: list[dict], t: Tokens = LIGHT) -> go.Figure:
    """İstasyonlar, yarınki tahmin kategorisinin rengiyle (kenarlıkla, her iki temada seçilir)."""
    df = pd.DataFrame(rows)
    text = [f"<b>{escape(r['name'])}</b><br>Yarın bu saatte: {tr_num(r['pm25'], 0)} µg/m³"
            f"<br>{escape(r['category'])}"
            + ("<br><b>Uyarı</b>" if r["is_alert"] else "")
            + ("<br>Uyarı riski: aralığın üst sınırı 35,5'i aşıyor"
               if r["risk"] and not r["is_alert"] else "")
            for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scattermap(lat=df["lat"], lon=df["lon"], mode="markers", name="kenar",
                                marker={"size": 22, "color": t.measured, "opacity": 0.85},
                                hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scattermap(
        lat=df["lat"], lon=df["lon"], mode="markers", name="istasyonlar",
        marker={"size": 17, "color": [category_color(c) for c in df["category"]]},
        text=text, hoverinfo="text", showlegend=False))
    style = "carto-darkmatter" if t.name == "dark" else "carto-positron"
    fig.update_layout(**plotly_layout(
        t, height=440, map={"style": style, "center": {"lat": 39.7, "lon": 30.6}, "zoom": 5.1},
        margin={"l": 0, "r": 0, "t": 0, "b": 0}))
    return fig


PCT_TICKS = {"tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
             "ticktext": ["%0", "%20", "%40", "%60", "%80", "%100"]}   # Türkçe: %80


def pr_figure(curves: dict, operating: dict | None, t: Tokens = LIGHT) -> go.Figure:
    """Uyarı yakalama (recall) / doğru uyarı oranı (precision) dengesi. Yüzdeler Türkçe
    biçimde ('%80') önceden metne çevrilir; Plotly'nin '.0%' biçimi '80%' üretir."""
    fig = go.Figure()
    styles = {"lgbm_gercekci": {"color": t.data, "width": 3},
              "lgbm_iyimser": {"color": t.data, "width": 1.5, "dash": "dot"}}
    hover = ("Karar eşiği: %{customdata[0]} µg/m³<br>Yakalama: %{customdata[1]}"
             "<br>İsabet: %{customdata[2]}<extra></extra>")
    for m, c in curves["pr"].items():
        custom = [[tr_num(th), tr_pct(r), tr_pct(p)]
                  for th, r, p in zip(c["threshold"], c["recall"], c["precision"], strict=True)]
        fig.add_trace(go.Scatter(
            x=c["recall"], y=c["precision"], mode="lines", name=MODEL_LABELS.get(m, m),
            line=styles.get(m, {}), customdata=custom, hovertemplate=hover))
    symbols = {"persistence": "square", "cams_raw": "x", "cams_scaled": "diamond"}
    for m, p in curves["points"].items():
        fig.add_trace(go.Scatter(
            x=[p["recall"]], y=[p["precision"]], mode="markers+text", name=MODEL_LABELS[m],
            text=[MODEL_LABELS[m]], textposition="bottom center",
            textfont={"color": t.muted, "size": 11},
            marker={"size": 11, "symbol": symbols[m], "color": t.muted},
            hovertemplate=(f"Yakalama: {tr_pct(p['recall'])}<br>İsabet: "
                           f"{tr_pct(p['precision'])}<extra>{MODEL_LABELS[m]}</extra>")))
    if operating:
        fig.add_trace(go.Scatter(
            x=[operating["recall"]], y=[operating["precision"]], mode="markers+text",
            name="Canlı sistem (istasyon eşikleri)", text=["canlı sistem"],
            textposition="top right", textfont={"color": t.text, "size": 11},
            marker={"size": 14, "color": t.data, "line": {"color": t.surface, "width": 2}},
            hovertemplate=(f"Yakalama: {tr_pct(operating['recall'])}<br>İsabet: "
                           f"{tr_pct(operating['precision'])}<extra>Canlı sistem</extra>")))
    fig.update_layout(**plotly_layout(
        t, height=380, legend={"orientation": "h", "y": -0.22, "x": 0},
        xaxis={"title": {"text": "yakalanan uyarı oranı (recall)"}, "range": [0, 1.02],
               **PCT_TICKS},
        yaxis={"title": {"text": "doğru uyarı oranı (precision)"}, "range": [0, 1.02],
               **PCT_TICKS}))
    return fig


def calibration_figure(curves: dict, t: Tokens = LIGHT) -> go.Figure:
    c = curves["calibration"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 120], y=[0, 120], mode="lines", name="kusursuz tahmin",
                             line={"color": t.muted, "dash": "dot", "width": 1},
                             hoverinfo="skip"))
    styles = {"lgbm_gercekci": {"color": t.data, "width": 3},
              "persistence": {"color": t.muted, "width": 1.5, "dash": "dash"},
              "cams_raw": {"color": t.increase, "width": 1.5}}
    for m in ("lgbm_gercekci", "persistence", "cams_raw"):
        fig.add_trace(go.Scatter(x=c["true_mid"], y=c[m], mode="lines",
                                 name=MODEL_LABELS[m], line=styles[m],
                                 hovertemplate="Gerçek: %{x:.1f} µg/m³<br>Ortalama tahmin: "
                                               "%{y:.1f} µg/m³<extra>" + MODEL_LABELS[m]
                                               + "</extra>"))
    fig.update_layout(**plotly_layout(
        t, height=380, legend={"orientation": "h", "y": -0.22, "x": 0},
        xaxis={"title": {"text": "gerçek PM2.5 (µg/m³)"}, "range": [0, 120]},
        yaxis={"title": {"text": "ortalama tahmin (µg/m³)"}, "range": [0, 120]}))
    return fig


def families_figure(shares: dict[str, float], t: Tokens = LIGHT) -> go.Figure:
    items = sorted(shares.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(
        x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
        marker_color=[t.data if v >= 10 else t.muted for _, v in items],
        text=[f"%{tr_num(v)}" for _, v in items], textposition="outside",
        textfont={"color": t.text}, hovertemplate="%{y}: %%{x:.1f}<extra></extra>"))
    fig.update_layout(**plotly_layout(
        t, height=320, showlegend=False,
        xaxis={"title": {"text": "tahmine katkı payı (%)"},
               "range": [0, max(v for _, v in items) * 1.2]},
        yaxis={"tickfont": {"color": t.text}}))
    return fig
